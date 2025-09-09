import os
import sqlite3
import sys
from werkzeug.security import generate_password_hash


def main():
    if len(sys.argv) < 3:
        print("Usage: python scripts/set_admin.py <new_email> <new_password> [new_name]", file=sys.stderr)
        sys.exit(1)

    new_email = sys.argv[1].strip().lower()
    new_password = sys.argv[2]
    new_name = (sys.argv[3].strip() if len(sys.argv) > 3 else None)

    db_path = os.path.join("instance", "app.db")
    if not os.path.exists(db_path):
        print(f"DB not found at {db_path}")
        sys.exit(1)

    con = sqlite3.connect(db_path)
    cur = con.cursor()

    # Find first admin
    row = cur.execute("SELECT id, email, name FROM user WHERE role = 'admin' ORDER BY id ASC LIMIT 1").fetchone()
    if not row:
        print("No admin user found.")
        sys.exit(1)

    uid, old_email, old_name = row
    # Ensure email unique
    exists = cur.execute("SELECT 1 FROM user WHERE email = ? AND id != ?", (new_email, uid)).fetchone()
    if exists:
        print("Email already in use by another user.")
        sys.exit(1)

    pwd_hash = generate_password_hash(new_password)
    name_to_set = new_name if new_name else old_name

    cur.execute("UPDATE user SET email = ?, name = ?, password_hash = ? WHERE id = ?", (new_email, name_to_set, pwd_hash, uid))
    con.commit()
    print(f"Updated admin {uid}: {old_email} -> {new_email}, name: {old_name} -> {name_to_set}")


if __name__ == "__main__":
    main()

