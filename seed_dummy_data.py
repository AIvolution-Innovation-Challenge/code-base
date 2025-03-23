import sqlite3
import random
import uuid
from datetime import datetime, timedelta

conn = sqlite3.connect("documents.db")
cursor = conn.cursor()

# Create results table if it doesn't exist
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

# Create chat_logs table if it doesn't exist
cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_logs (
        id TEXT,
        business_role TEXT,
        message TEXT,
        timestamp TEXT
    )
""")

roles = ["HR Associate", "IT Analyst", "Marketing Intern"]
documents = ["Leave Policy", "IT Security Handbook", "Employee Code of Conduct"]

# Clear old data (for testing)
cursor.execute("DELETE FROM results")
cursor.execute("DELETE FROM chat_logs")
conn.commit()

# ✅ Track generated IDs to ensure uniqueness
generated_ids = set()

# Seed quiz results
for role in roles:
    for doc in documents:
        for _ in range(12):  
            while True:  # Ensure unique ID
                user_id = f"{role.replace(' ', '')}_{random.randint(1000,9999)}"
                if user_id not in generated_ids:
                    generated_ids.add(user_id)
                    break
            
            score = random.randint(60, 100)
            total = 100  
            submitted = datetime.now() - timedelta(days=random.randint(1, 14))

            cursor.execute("""
                INSERT INTO results (id, business_role, document_title, score, total, submission_time)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, role, doc, score, total, submitted.strftime("%Y-%m-%d %H:%M:%S")))

# Seed chat logs
common_questions = [
    "How many sick leaves do we get?",
    "Who do I contact for IT setup?",
    "What's the dress code?",
    "Can I carry forward unused leave?",
    "Is remote work allowed?"
]

for role in roles:
    for _ in range(10):  
        user_id = f"{role.replace(' ', '')}_{uuid.uuid4().hex[:8]}"  # ✅ Guaranteed unique
        message = random.choice(common_questions)
        timestamp = datetime.now() - timedelta(days=random.randint(1, 14), hours=random.randint(0, 23))

        cursor.execute("""
            INSERT INTO chat_logs (id, business_role, message, timestamp)
            VALUES (?, ?, ?, ?)
        """, (user_id, role, message, timestamp.strftime("%Y-%m-%d %H:%M:%S")))

conn.commit()
conn.close()

print("✅ Dummy data seeded successfully!")

