import sqlite3
import hashlib
import os
from datetime import date, datetime, timedelta

DB_PATH = "accountability.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL DEFAULT 1,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT,
            difficulty INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            active INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Migration: add user_id column if it doesn't exist yet
    try:
        c.execute("ALTER TABLE goals ADD COLUMN user_id INTEGER NOT NULL DEFAULT 1")
        conn.commit()
    except Exception:
        pass

    c.execute("""
        CREATE TABLE IF NOT EXISTS daily_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal_id INTEGER NOT NULL,
            plan_date TEXT NOT NULL,
            plan_text TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (goal_id) REFERENCES goals(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS check_ins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal_id INTEGER NOT NULL,
            check_in_date TEXT NOT NULL,
            completed INTEGER NOT NULL,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (goal_id) REFERENCES goals(id)
        )
    """)

    conn.commit()
    conn.close()


# --- Auth ---

def _hash_password(password: str) -> str:
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
    return salt.hex() + ":" + key.hex()


def _verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt_hex, key_hex = stored_hash.split(":")
        salt = bytes.fromhex(salt_hex)
        key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
        return key.hex() == key_hex
    except Exception:
        return False


def create_user(username: str, password: str):
    """Returns user dict on success, raises ValueError on duplicate username."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username.strip().lower(), _hash_password(password)),
        )
        conn.commit()
        user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        return {"id": user_id, "username": username.strip().lower()}
    except sqlite3.IntegrityError:
        raise ValueError("Username already taken. Choose a different one.")
    finally:
        conn.close()


def login_user(username: str, password: str):
    """Returns user dict on success, None on failure."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE username = ?", (username.strip().lower(),)
    ).fetchone()
    conn.close()
    if row and _verify_password(password, row["password_hash"]):
        return {"id": row["id"], "username": row["username"]}
    return None


# --- Goal operations ---

def create_goal(title, description, category, user_id):
    conn = get_connection()
    conn.execute(
        "INSERT INTO goals (title, description, category, user_id) VALUES (?, ?, ?, ?)",
        (title, description, category, user_id),
    )
    conn.commit()
    goal_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return goal_id


def get_active_goals(user_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM goals WHERE active = 1 AND user_id = ? ORDER BY created_at DESC",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_goal(goal_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM goals WHERE id = ?", (goal_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def deactivate_goal(goal_id):
    conn = get_connection()
    conn.execute("UPDATE goals SET active = 0 WHERE id = ?", (goal_id,))
    conn.commit()
    conn.close()


def update_difficulty(goal_id, difficulty):
    conn = get_connection()
    conn.execute(
        "UPDATE goals SET difficulty = ? WHERE id = ?", (difficulty, goal_id)
    )
    conn.commit()
    conn.close()


# --- Daily plan operations ---

def save_plan(goal_id, plan_text, plan_date=None):
    if plan_date is None:
        plan_date = str(date.today())
    conn = get_connection()
    conn.execute(
        "INSERT INTO daily_plans (goal_id, plan_date, plan_text) VALUES (?, ?, ?)",
        (goal_id, plan_date, plan_text),
    )
    conn.commit()
    conn.close()


def get_plan_for_date(goal_id, plan_date=None):
    if plan_date is None:
        plan_date = str(date.today())
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM daily_plans WHERE goal_id = ? AND plan_date = ? ORDER BY id DESC LIMIT 1",
        (goal_id, plan_date),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# --- Check-in operations ---

def save_check_in(goal_id, completed, notes=""):
    today = str(date.today())
    conn = get_connection()
    conn.execute(
        "DELETE FROM check_ins WHERE goal_id = ? AND check_in_date = ?",
        (goal_id, today),
    )
    conn.execute(
        "INSERT INTO check_ins (goal_id, check_in_date, completed, notes) VALUES (?, ?, ?, ?)",
        (goal_id, today, int(completed), notes),
    )
    conn.commit()
    conn.close()


def get_check_in_for_date(goal_id, check_date=None):
    if check_date is None:
        check_date = str(date.today())
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM check_ins WHERE goal_id = ? AND check_in_date = ?",
        (goal_id, check_date),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_check_ins(goal_id, days=30):
    since = str(date.today() - timedelta(days=days))
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM check_ins WHERE goal_id = ? AND check_in_date >= ? ORDER BY check_in_date DESC",
        (goal_id, since),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- Stats ---

def compute_stats(goal_id):
    check_ins = get_check_ins(goal_id, days=90)

    if not check_ins:
        return {"streak": 0, "completion_rate": 0.0, "consistency_score": 0.0, "missed_days": 0, "total_days": 0}

    history = {ci["check_in_date"]: bool(ci["completed"]) for ci in check_ins}

    streak = 0
    check_date = date.today()
    while True:
        key = str(check_date)
        if key in history and history[key]:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break

    total = len(check_ins)
    completed = sum(1 for ci in check_ins if ci["completed"])
    missed = total - completed
    completion_rate = round(completed / total * 100, 1) if total > 0 else 0.0
    consistency_score = round(min(100.0, streak * 5 + completion_rate * 0.5), 1)

    return {
        "streak": streak,
        "completion_rate": completion_rate,
        "consistency_score": consistency_score,
        "missed_days": missed,
        "total_days": total,
    }


def maybe_adapt_difficulty(goal_id):
    goal = get_goal(goal_id)
    if not goal:
        return None

    recent = get_check_ins(goal_id, days=7)
    if len(recent) < 5:
        return None

    rate = sum(1 for ci in recent if ci["completed"]) / len(recent) * 100
    current = goal["difficulty"]

    if rate >= 80 and current < 5:
        new_diff = current + 1
        update_difficulty(goal_id, new_diff)
        return new_diff
    elif rate <= 40 and current > 1:
        new_diff = current - 1
        update_difficulty(goal_id, new_diff)
        return new_diff

    return None
