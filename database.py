"""
database.py
All SQLite access for Memory Bridge lives here so the UI code
never has to write raw SQL. The database file is created
automatically on first run inside the data/ folder.

Multi-user support: every data table has a user_id column.
All helpers accept a user_id parameter to scope queries.
"""

import sqlite3
import os
import sys
import hashlib
from datetime import datetime, date, timedelta

# When packaged by PyInstaller (--onefile), __file__ points to a temp extraction
# folder that is deleted after the app closes. We store the database next to
# the .exe so that user data persists between runs.
if getattr(sys, 'frozen', False):
    # Running as compiled .exe
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    # Running from source
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(_BASE_DIR, "data", "memory_bridge.db")



def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    # ── Users ──────────────────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""")

    # ── Medicines ──────────────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS medicines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL DEFAULT 1,
        name TEXT NOT NULL,
        purpose TEXT,
        dosage TEXT,
        timing TEXT,
        food_instruction TEXT,
        remaining_tablets INTEGER DEFAULT 0,
        doctor TEXT,
        photo_path TEXT,
        taken_today INTEGER DEFAULT 0,
        last_taken TEXT,
        start_date TEXT,
        end_date TEXT,
        frequency TEXT DEFAULT 'Daily'
    )""")

    # ── Medicine daily logs ────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS medicine_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL DEFAULT 1,
        medicine_id INTEGER NOT NULL,
        taken_date TEXT NOT NULL,
        taken_time TEXT NOT NULL
    )""")

    # ── Schedule ───────────────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL DEFAULT 1,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        title TEXT NOT NULL,
        period TEXT,
        status TEXT DEFAULT 'Pending'
    )""")

    # ── Family ────────────────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS family (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL DEFAULT 1,
        name TEXT NOT NULL,
        relationship TEXT,
        phone TEXT,
        birthday TEXT,
        photo_path TEXT,
        notes TEXT,
        is_emergency_contact INTEGER DEFAULT 0
    )""")

    # ── Appointments ──────────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL DEFAULT 1,
        title TEXT NOT NULL,
        date TEXT NOT NULL,
        time TEXT,
        description TEXT,
        kind TEXT DEFAULT 'Appointment'
    )""")

    # ── Bills ─────────────────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS bills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL DEFAULT 1,
        name TEXT NOT NULL,
        due_date TEXT,
        amount TEXT,
        paid INTEGER DEFAULT 0
    )""")

    # ── Health records ────────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS health_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL DEFAULT 1,
        type TEXT NOT NULL,
        value TEXT NOT NULL,
        date TEXT NOT NULL
    )""")

    # ── Lost items ────────────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS lost_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL DEFAULT 1,
        name TEXT NOT NULL,
        location TEXT,
        photo_path TEXT,
        date_saved TEXT,
        note TEXT
    )""")

    # ── Voice notes ───────────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS voice_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL DEFAULT 1,
        text TEXT NOT NULL,
        created_at TEXT NOT NULL,
        reminded INTEGER DEFAULT 0
    )""")

    # ── Settings (per-user key/value) ─────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS settings (
        user_id INTEGER NOT NULL DEFAULT 1,
        key TEXT NOT NULL,
        value TEXT,
        PRIMARY KEY (user_id, key)
    )""")

    # ── Mood log ──────────────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS mood_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL DEFAULT 1,
        date TEXT NOT NULL,
        mood TEXT NOT NULL
    )""")

    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# USER AUTHENTICATION
# ─────────────────────────────────────────────────────────────────────────────

def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def register_user(name: str, email: str, password: str):
    """Register a new user. Returns (True, user_id) or (False, error_message)."""
    existing = query("SELECT id FROM users WHERE email=?", (email.lower().strip(),))
    if existing:
        return False, "An account with this email already exists."
    try:
        uid = execute(
            "INSERT INTO users (name, email, password_hash, created_at) VALUES (?,?,?,?)",
            (name.strip(), email.lower().strip(), _hash_password(password),
             datetime.now().isoformat())
        )
        _seed_user_data(uid)
        return True, uid
    except Exception as e:
        return False, str(e)


def verify_user(email: str, password: str):
    """Returns user row if credentials match, else None."""
    rows = query("SELECT * FROM users WHERE email=?", (email.lower().strip(),))
    if not rows:
        return None
    user = rows[0]
    if user["password_hash"] == _hash_password(password):
        return user
    return None


def get_user_by_id(user_id: int):
    rows = query("SELECT * FROM users WHERE id=?", (user_id,))
    return rows[0] if rows else None


def _seed_user_data(user_id: int):
    """Add demo data for a brand-new user."""
    conn = get_connection()
    c = conn.cursor()
    today = date.today().isoformat()
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    day_after = (date.today() + timedelta(days=2)).isoformat()

    # Sample medicines
    c.execute("""INSERT INTO medicines
        (user_id, name, purpose, dosage, timing, food_instruction, remaining_tablets, doctor, start_date, end_date, frequency)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (user_id, "Amlodipine", "Blood Pressure", "1 tablet", "08:00 AM",
         "After breakfast", 18, "Dr. Rahman", today,
         (date.today() + timedelta(days=30)).isoformat(), "Daily"))
    c.execute("""INSERT INTO medicines
        (user_id, name, purpose, dosage, timing, food_instruction, remaining_tablets, doctor, start_date, end_date, frequency)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (user_id, "Metformin", "Diabetes", "1 tablet", "08:00 PM",
         "After dinner", 25, "Dr. Rahman", today,
         (date.today() + timedelta(days=30)).isoformat(), "Daily"))
    c.execute("""INSERT INTO medicines
        (user_id, name, purpose, dosage, timing, food_instruction, remaining_tablets, doctor, start_date, end_date, frequency)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (user_id, "Vitamin D", "Supplement", "1 capsule", "09:00 AM",
         "With breakfast", 30, "Dr. Rahman", today,
         (date.today() + timedelta(days=30)).isoformat(), "Daily"))

    # Sample schedule — today + upcoming days
    for sched_date, stime, stitle, speriod in [
        (today,      "07:00 AM", "Drink a glass of water",       "Morning"),
        (today,      "08:00 AM", "Take blood pressure medicine",  "Morning"),
        (today,      "03:00 PM", "Doctor appointment",            "Afternoon"),
        (today,      "08:00 PM", "Take diabetes medicine",        "Night"),
        (today,      "09:30 PM", "Lock the doors",                "Night"),
        (tomorrow,   "08:00 AM", "Morning walk",                  "Morning"),
        (tomorrow,   "10:00 AM", "Call family",                   "Morning"),
        (day_after,  "09:00 AM", "Eye doctor visit",              "Morning"),
        (day_after,  "06:00 PM", "Evening yoga",                  "Evening"),
    ]:
        c.execute("INSERT INTO schedule (user_id, date, time, title, period, status) VALUES (?,?,?,?,?,?)",
                  (user_id, sched_date, stime, stitle, speriod, "Pending"))

    # Family
    c.execute("""INSERT INTO family (user_id, name, relationship, phone, birthday, is_emergency_contact)
                 VALUES (?,?,?,?,?,?)""", (user_id, "Sarah", "Daughter", "+880 1XXXXXXXXX", "15 August", 1))
    c.execute("""INSERT INTO family (user_id, name, relationship, phone, birthday, is_emergency_contact)
                 VALUES (?,?,?,?,?,?)""", (user_id, "Rafiq", "Son", "+880 1XXXXXXXXX", "02 March", 1))

    # Appointments
    c.execute("INSERT INTO appointments (user_id, title, date, time, description, kind) VALUES (?,?,?,?,?,?)",
              (user_id, "Doctor Visit", today, "03:00 PM", "General checkup", "Doctor"))

    # Bills
    c.execute("INSERT INTO bills (user_id, name, due_date, amount, paid) VALUES (?,?,?,?,?)",
              (user_id, "Electricity Bill", today, "1200 BDT", 0))

    # Lost items
    c.execute("INSERT INTO lost_items (user_id, name, location, date_saved) VALUES (?,?,?,?)",
              (user_id, "Glasses", "On the kitchen table", today))
    c.execute("INSERT INTO lost_items (user_id, name, location, date_saved) VALUES (?,?,?,?)",
              (user_id, "House Keys", "Blue drawer in bedroom", today))

    # Per-user settings
    for k, v in [
        ("appearance_mode", "Light"),
        ("font_scale", "1.0"),
        ("voice_enabled", "1"),
        ("user_name", "Friend"),
        ("water_target", "8"),
        ("water_count", "0"),
        ("water_date", today),
    ]:
        c.execute("INSERT OR IGNORE INTO settings (user_id, key, value) VALUES (?,?,?)",
                  (user_id, k, v))

    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# GENERIC HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def query(sql, params=()):
    conn = get_connection()
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return rows


def execute(sql, params=()):
    conn = get_connection()
    cur = conn.execute(sql, params)
    conn.commit()
    last_id = cur.lastrowid
    conn.close()
    return last_id


def get_setting(key, default=None, user_id=1):
    rows = query("SELECT value FROM settings WHERE user_id=? AND key=?", (user_id, key))
    return rows[0]["value"] if rows else default


def set_setting(key, value, user_id=1):
    execute("""INSERT INTO settings (user_id, key, value) VALUES (?, ?, ?)
               ON CONFLICT(user_id, key) DO UPDATE SET value=excluded.value""",
            (user_id, key, str(value)))


# ─────────────────────────────────────────────────────────────────────────────
# MEDICINE HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def get_medicines_for_date(user_id: int, target_date: str):
    """Return medicines active on a given date (start_date <= target <= end_date)."""
    return query("""
        SELECT m.*,
               (SELECT COUNT(*) FROM medicine_logs ml
                WHERE ml.medicine_id=m.id AND ml.taken_date=? AND ml.user_id=?) AS taken_on_date
        FROM medicines m
        WHERE m.user_id=?
          AND (m.start_date IS NULL OR m.start_date <= ?)
          AND (m.end_date IS NULL OR m.end_date >= ?)
        ORDER BY m.timing
    """, (target_date, user_id, user_id, target_date, target_date))


def log_medicine_taken(user_id: int, medicine_id: int, taken_date: str, taken_time: str):
    """Log a medicine as taken for a specific date."""
    # Avoid duplicate log for same day
    existing = query("SELECT id FROM medicine_logs WHERE user_id=? AND medicine_id=? AND taken_date=?",
                     (user_id, medicine_id, taken_date))
    if not existing:
        execute("INSERT INTO medicine_logs (user_id, medicine_id, taken_date, taken_time) VALUES (?,?,?,?)",
                (user_id, medicine_id, taken_date, taken_time))
    # Also update today flag if today
    if taken_date == date.today().isoformat():
        execute("UPDATE medicines SET taken_today=1, last_taken=? WHERE id=? AND user_id=?",
                (taken_time, medicine_id, user_id))
    execute("UPDATE medicines SET remaining_tablets=MAX(remaining_tablets-1,0) WHERE id=? AND user_id=?",
            (medicine_id, user_id))


# ─────────────────────────────────────────────────────────────────────────────
# SCHEDULE HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def get_upcoming_schedule(user_id: int, days: int = 5):
    """Return all scheduled tasks for the next `days` days."""
    today = date.today().isoformat()
    end_date = (date.today() + timedelta(days=days - 1)).isoformat()
    return query("""
        SELECT * FROM schedule
        WHERE user_id=? AND date >= ? AND date <= ?
        ORDER BY date, time
    """, (user_id, today, end_date))
