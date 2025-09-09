import os, sqlite3, json, sys

DB_PATH = os.path.join('instance', 'app.db')

if not os.path.exists(DB_PATH):
    print(json.dumps({"error": "db_not_found", "path": DB_PATH}))
    sys.exit(0)

con = sqlite3.connect(DB_PATH)
cur = con.cursor()
try:
    cur.execute("SELECT id, email, name, role FROM user")
    rows = cur.fetchall()
except Exception as e:
    print(json.dumps({"error": str(e)}))
    sys.exit(1)

users = [
    {"id": r[0], "email": r[1], "name": r[2], "role": r[3]}
    for r in rows
]
admins = [u for u in users if u["role"] == "admin"]

print(json.dumps({"admins": admins, "users": users}, ensure_ascii=False))

