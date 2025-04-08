# seed_dummy_data.py
import sqlite3
import random
import uuid
from datetime import datetime, timedelta

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# Create required tables
cursor.execute("""
    CREATE TABLE IF NOT EXISTS results (
        id TEXT PRIMARY KEY,
        document_title TEXT,
        business_role TEXT,
        score INTEGER,
        total INTEGER,
        submission_time TEXT
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_logs (
        id TEXT,
        business_role TEXT,
        message TEXT,
        timestamp TEXT
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        system_role TEXT NOT NULL,
        business_role TEXT NOT NULL,
        department TEXT,
        start_date TEXT
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY,
        document_title TEXT,
        business_role TEXT,
        question TEXT,
        options TEXT,
        answer TEXT
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
""")

cursor.execute("SELECT * FROM settings WHERE key = 'quiz_deadline_days'")
if cursor.fetchone() is None:
    cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?)", ("quiz_deadline_days", "7"))

# Role-to-department and role-to-documents mapping
role_dept_map = {
    "HR Associate": "HR",
    "IT Analyst": "IT",
    "Marketing Intern": "Marketing"
}

role_docs_map = {
    "HR Associate": ["Leave Policy", "Workplace Guidelines"],
    "IT Analyst": ["IT Security Handbook", "Data Privacy Policy"],
    "Marketing Intern": ["Brand Voice Guide", "Social Media Policy"]
}

roles = list(role_dept_map.keys())

# Reset tables
cursor.execute("DELETE FROM results")
cursor.execute("DELETE FROM chat_logs")
cursor.execute("DELETE FROM users")
cursor.execute("DELETE FROM questions")
conn.commit()

# Generate users
defaulters = []
compliant_users = []
today = datetime.today()

for i in range(1, 21):
    username = f"user{i}"
    password = "password"
    system_role = "employee"
    role = random.choice(roles)
    department = role_dept_map[role]

    if i <= 5:
        start_date = (today - timedelta(days=10)).strftime("%Y-%m-%d")
        defaulters.append((username, role))
    else:
        start_date = (today - timedelta(days=random.randint(0, 6))).strftime("%Y-%m-%d")
        compliant_users.append((username, role))

    cursor.execute("""
        INSERT INTO users (username, password, system_role, business_role, department, start_date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (username, password, system_role, role, department, start_date))

# Insert results for compliant users
for username, role in compliant_users:
    docs = role_docs_map[role]
    for doc in docs:
        result_id = f"{username}_{doc.replace(' ', '')}"
        score = random.randint(70, 100)
        submitted = today - timedelta(days=random.randint(1, 6))
        cursor.execute("""
            INSERT INTO results (id, document_title, business_role, score, total, submission_time)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (result_id, doc, role, score, 100, submitted.strftime("%Y-%m-%d %H:%M:%S")))

# Insert questions for each doc per role
sample_question = "What is the purpose of this document?"
sample_options = "A. Info|B. Rules|C. Both|D. None"
sample_answer = "C"

for role, docs in role_docs_map.items():
    for doc in docs:
        cursor.execute("""
            INSERT INTO questions (document_title, business_role, question, options, answer)
            VALUES (?, ?, ?, ?, ?)
        """, (doc, role, sample_question, sample_options, sample_answer))

# Insert chat logs
common_questions = [
    "How many sick leaves do we get?",
    "Who do I contact for IT setup?",
    "What's the dress code?",
    "Can I carry forward unused leave?",
    "Is remote work allowed?"
]

for role in roles:
    for _ in range(10):
        user_id = f"{role.replace(' ', '')}_{uuid.uuid4().hex[:8]}"
        message = random.choice(common_questions)
        timestamp = datetime.now() - timedelta(days=random.randint(1, 14), hours=random.randint(0, 23))
        cursor.execute("""
            INSERT INTO chat_logs (id, business_role, message, timestamp)
            VALUES (?, ?, ?, ?)
        """, (user_id, role, message, timestamp.strftime("%Y-%m-%d %H:%M:%S")))

conn.commit()
conn.close()
print("Dummy data seeded successfully!")
