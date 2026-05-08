import sqlite3
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
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT,
            difficulty INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            active INTEGER DEFAULT 1
        )
    """)

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


# --- Goal operations ---

def create_goal(title, description, category):
    conn = get_connection()
    conn.execute(
        "INSERT INTO goals (title, description, category) VALUES (?, ?, ?)",
        (title, description, category),
    )
    conn.commit()
    goal_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return goal_id


def get_active_goals():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM goals WHERE active = 1 ORDER BY created_at DESC"
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
    # Upsert: delete any existing check-in for today then insert
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
    """Returns streak, completion_rate, consistency_score, missed_days."""
    check_ins = get_check_ins(goal_id, days=90)

    if not check_ins:
        return {"streak": 0, "completion_rate": 0.0, "consistency_score": 0.0, "missed_days": 0, "total_days": 0}

    # Map date -> completed
    history = {ci["check_in_date"]: bool(ci["completed"]) for ci in check_ins}

    # Streak: consecutive completed days ending today (or yesterday)
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

    # Consistency score: weighted blend of streak and completion rate
    consistency_score = round(min(100.0, streak * 5 + completion_rate * 0.5), 1)

    return {
        "streak": streak,
        "completion_rate": completion_rate,
        "consistency_score": consistency_score,
        "missed_days": missed,
        "total_days": total,
    }


def maybe_adapt_difficulty(goal_id):
    """Increase difficulty if doing great, decrease if struggling. Returns new difficulty or None."""
    goal = get_goal(goal_id)
    if not goal:
        return None

    recent = get_check_ins(goal_id, days=7)
    if len(recent) < 5:
        return None  # not enough data

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
