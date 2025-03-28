# db_utils.py

import sqlite3

def get_connection(db_name='documents.db'):
    return sqlite3.connect(db_name, check_same_thread=False)

def initialize_database(conn):
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
            id TEXT PRIMARY KEY,
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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            user_id TEXT,
            page TEXT,
            action TEXT,
            details TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mistakes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            question TEXT,
            correct_answer TEXT,
            user_answer TEXT,
            timestamp TEXT
        )
    ''')

    conn.commit()
    return conn, cursor
