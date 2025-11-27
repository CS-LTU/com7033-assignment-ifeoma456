import os
import sqlite3
from flask import g

DATABASE = os.getenv('DATABASE_URI', os.path.join(os.path.dirname(__file__), '..', '..', 'app.db'))

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES)
        db.row_factory = sqlite3.Row
        g._database = db
    return db

def close_db(e=None):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
        g._database = None

def init_db():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.executescript('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY,
        gender TEXT,
        age REAL,
        hypertension INTEGER,
        heart_disease INTEGER,
        ever_married TEXT,
        work_type TEXT,
        Residence_type TEXT,
        avg_glucose_level REAL,
        bmi REAL,
        smoking_status TEXT,
        stroke INTEGER
    );
    ''')
    conn.commit()
    conn.close()