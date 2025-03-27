import sqlite3
from datetime import datetime

class AppLogger:
    def __init__(self, db_path="documents.db"):
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self):
        """Ensure the logs and mistakes tables exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
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

    def log_event(self, user_id, page, action, details=""):
        """Insert a log entry into the database."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO logs (timestamp, user_id, page, action, details)
                VALUES (?, ?, ?, ?, ?)
            ''', (timestamp, user_id, page, action, details))
            conn.commit()

    def log_mistakes(self, user_id, mistakes):
        """Log mistakes in a separate table."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for mistake in mistakes:
                cursor.execute('''
                    INSERT INTO mistakes (user_id, question, correct_answer, user_answer, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, mistake['question'], mistake['correct_answer'], mistake['user_answer'], timestamp))
            conn.commit()
