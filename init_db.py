# init_db.py

import sqlite3

def init_db(db_path="documents.db"):
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_docs (
            id INTEGER PRIMARY KEY,
            page_content TEXT,
            metadata TEXT,
            business_role TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY,
            document_title TEXT,
            business_role TEXT,
            question TEXT,
            options TEXT,
            answer TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY,
            document_title TEXT,
            business_role TEXT,
            score INTEGER,
            total INTEGER,
            submission_time TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')

    conn.commit()
    return conn, cursor
