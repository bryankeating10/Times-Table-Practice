-- SQLite schema
CREATE TABLE multiplication_table (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  multiplicand INTEGER NOT NULL,
  multiplier INTEGER NOT NULL,
  product INTEGER NOT NULL,
  UNIQUE (multiplicand, multiplier)
);
CREATE INDEX idx_mt_product ON multiplication_table (product);
CREATE INDEX idx_mt_pair ON multiplication_table (multiplicand, multiplier);

CREATE TABLE user_progress (
  user_id INTEGER NOT NULL,
  multiplicand INTEGER NOT NULL,
  multiplier INTEGER NOT NULL,
  attempts INTEGER DEFAULT 0,
  correct INTEGER DEFAULT 0,
  last_attempt TEXT,
  PRIMARY KEY (user_id, multiplicand, multiplier)
);
CREATE INDEX idx_up_user ON user_progress (user_id);
