# app.py - Flask + SQLite single-file app
# Run: python app.py
from flask import Flask, g, request, jsonify
import sqlite3
import os

DB_PATH = "multiplication.db"
MASTERy_THRESHOLD_DEFAULT = 3

app = Flask(__name__)

def get_db():
    db = getattr(g, "_db", None)
    if db is None:
        must_init = not os.path.exists(DB_PATH)
        db = g._db = sqlite3.connect(DB_PATH, check_same_thread=False)
        db.row_factory = sqlite3.Row
        if must_init:
            init_db(db)
    return db

def init_db(db):
    cur = db.cursor()
    # create tables
    cur.executescript(""" 
    CREATE TABLE IF NOT EXISTS multiplication_table (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      multiplicand INTEGER NOT NULL,
      multiplier INTEGER NOT NULL,
      product INTEGER NOT NULL,
      UNIQUE (multiplicand, multiplier)
    );
    CREATE INDEX IF NOT EXISTS idx_mt_product ON multiplication_table (product);
    CREATE INDEX IF NOT EXISTS idx_mt_pair ON multiplication_table (multiplicand, multiplier);

    CREATE TABLE IF NOT EXISTS user_progress (
      user_id INTEGER NOT NULL,
      multiplicand INTEGER NOT NULL,
      multiplier INTEGER NOT NULL,
      attempts INTEGER DEFAULT 0,
      correct INTEGER DEFAULT 0,
      last_attempt TEXT,
      PRIMARY KEY (user_id, multiplicand, multiplier)
    );
    CREATE INDEX IF NOT EXISTS idx_up_user ON user_progress (user_id);
    """)
    # populate 1..30 x 1..30 if table is empty
    cur.execute("SELECT COUNT(*) AS c FROM multiplication_table")
    if cur.fetchone()["c"] == 0:
        rows = []
        for a in range(1,31):
            for b in range(1,31):
                rows.append((a,b,a*b))
        cur.executemany("INSERT OR IGNORE INTO multiplication_table (multiplicand, multiplier, product) VALUES (?, ?, ?)", rows)
    db.commit()

@app.teardown_appcontext
def close_db(e=None):
    db = getattr(g, "_db", None)
    if db is not None:
        db.close()

# Helper: parse comma-separated ints
def parse_int_list(s):
    if not s:
        return []
    return [int(x) for x in s.split(",") if x.strip().isdigit()]

@app.route("/api/problems", methods=["GET"])
def api_problems():
    """
    Query params:
      n (default 10)
      min_product, max_product
      exclude_factors (csv like 10,20,30)
      only_multiple_of (int)
      factor_x (int)  -> one factor equals X
      dedupe (0/1) -> multiplicand <= multiplier
      exclude_mastered (0/1)
      user_id (int, default 1)
      mastery_threshold (int, default 3)
    """
    db = get_db()
    n = int(request.args.get("n", 10))
    min_p = request.args.get("min_product")
    max_p = request.args.get("max_product")
    exclude_factors = parse_int_list(request.args.get("exclude_factors", ""))
    only_multiple_of = request.args.get("only_multiple_of")
    factor_x = request.args.get("factor_x")
    dedupe = request.args.get("dedupe", "0") == "1"
    exclude_mastered = request.args.get("exclude_mastered", "0") == "1"
    user_id = int(request.args.get("user_id", 1))
    mastery_threshold = int(request.args.get("mastery_threshold", MASTERy_THRESHOLD_DEFAULT))

    where = []
    params = []

    if min_p is not None:
        where.append("product >= ?"); params.append(int(min_p))
    if max_p is not None:
        where.append("product <= ?"); params.append(int(max_p))
    if exclude_factors:
        placeholders = ",".join("?" for _ in exclude_factors)
        where.append(f"multiplicand NOT IN ({placeholders})"); params.extend(exclude_factors)
        where.append(f"multiplier NOT IN ({placeholders})"); params.extend(exclude_factors)
    if only_multiple_of:
        mm = int(only_multiple_of)
        if mm != 0:
            where.append("product % ? = 0"); params.append(mm)
    if factor_x:
        x = int(factor_x)
        where.append("(multiplicand = ? OR multiplier = ?)"); params.extend([x,x])
    if dedupe:
        where.append("multiplicand <= multiplier")
    join_clause = ""
    if exclude_mastered:
        # LEFT JOIN to user_progress and require COALESCE(correct,0) < mastery_threshold
        join_clause = " LEFT JOIN user_progress p ON p.user_id = ? AND p.multiplicand = t.multiplicand AND p.multiplier = t.multiplier "
        params_for_master = [user_id]
        # we will put these params at the front of params list after join handling below
    # Build SQL
    base_sql = "SELECT t.multiplicand, t.multiplier, t.product FROM multiplication_table t"
    sql = base_sql + (join_clause if exclude_mastered else "")
    if exclude_mastered:
        # add COALESCE condition
        where.append("COALESCE(p.correct,0) < ?"); params_for_master.append(mastery_threshold)
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY RANDOM() LIMIT ?"
    # final params: if exclude_mastered then params_for_master first, then params, then limit
    final_params = []
    if exclude_mastered:
        final_params.extend(params_for_master)
    final_params.extend(params)
    final_params.append(n)
    cur = db.execute(sql, final_params)
    rows = [dict(r) for r in cur.fetchall()]
    return jsonify(rows)

@app.route("/api/attempt", methods=["POST"])
def api_attempt():
    """
    JSON body:
      user_id (int)
      multiplicand (int)
      multiplier (int)
      was_correct (bool)
    Performs upsert: increments attempts, increments correct if was_correct.
    """
    data = request.get_json(force=True)
    user_id = int(data.get("user_id", 1))
    a = int(data["multiplicand"])
    b = int(data["multiplier"])
    was_correct = bool(data.get("was_correct", False))
    correct_val = 1 if was_correct else 0
    db = get_db()
    cur = db.cursor()
    cur.execute("""
      INSERT INTO user_progress (user_id, multiplicand, multiplier, attempts, correct, last_attempt)
      VALUES (?, ?, ?, 1, ?, CURRENT_TIMESTAMP)
      ON CONFLICT(user_id, multiplicand, multiplier) DO UPDATE SET
        attempts = attempts + 1,
        correct = correct + excluded.correct,
        last_attempt = CURRENT_TIMESTAMP
    """, (user_id, a, b, correct_val))
    db.commit()
    return jsonify({"status": "ok"}), 201

@app.route("/api/progress", methods=["GET"])
def api_progress():
    """
    Query params:
      user_id (default 1)
      mastery_threshold (default 3)
    """
    db = get_db()
    user_id = int(request.args.get("user_id", 1))
    mastery_threshold = int(request.args.get("mastery_threshold", MASTERy_THRESHOLD_DEFAULT))
    cur = db.execute("""
      SELECT COALESCE(SUM(attempts),0) as total_attempts,
             COALESCE(SUM(correct),0) as total_correct,
             COALESCE(SUM(CASE WHEN correct >= ? THEN 1 ELSE 0 END),0) as mastered_count
      FROM user_progress WHERE user_id = ?
    """, (mastery_threshold, user_id))
    r = cur.fetchone()
    return jsonify(dict(r))

if __name__ == "__main__":
    # start server
    app.run(host="127.0.0.1", port=5000, debug=True)
