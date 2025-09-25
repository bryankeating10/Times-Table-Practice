# Setup (Linux / Mac)
python3 -m venv venv
source venv/bin/activate
pip install flask
python app.py
# open http://127.0.0.1:5000 in browser and serve index.html from same folder (e.g. open file directly or use simple http server)
# to serve index.html via simple server:
python -m http.server 8000
# then open http://127.0.0.1:8000/index.html

# Setup (Windows PowerShell)
python -m venv venv
venv\Scripts\Activate.ps1
pip install flask
python app.py

# Quick tests (after server started)
# Fetch 8 problems where one factor is 18 excluding factors 10,20,30:
curl "http://127.0.0.1:5000/api/problems?n=8&factor_x=18&exclude_factors=10,20,30&exclude_mastered=1&user_id=1"

# Mark an attempt (example: 18 x 5 correct)
curl -X POST -H "Content-Type: application/json" -d '{"user_id":1,"multiplicand":18,"multiplier":5,"was_correct":true}' http://127.0.0.1:5000/api/attempt

# Get progress
curl "http://127.0.0.1:5000/api/progress?user_id=1"

# Inspect DB with sqlite3 (optional)
sqlite3 multiplication.db "SELECT COUNT(*) FROM multiplication_table;"
sqlite3 multiplication.db "SELECT * FROM multiplication_table WHERE multiplicand=18 LIMIT 10;"