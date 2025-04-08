import sqlite3

# Dummy users data
dummy_users = {
    "junior": {"password": "employee", "role": "employee", "job":"business_analyst"},
    "senior": {"password": "employee", "role": "employee", "job":"business_analyst"},
    "employee": {"password": "employee", "role": "employee", "job":"business_analyst"},
    "admin": {"password": "admin", "role": "admin", "job":"admin"},
}

# Connect to (or create) the database
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Create the table if it doesn't already exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL,
        system_role TEXT NOT NULL,
        business_role TEXT NOT NULL
    )
''')

# Insert each user into the table. Using INSERT OR REPLACE allows updating if the username already exists.
for username, details in dummy_users.items():
    cursor.execute('''
        INSERT OR REPLACE INTO users (username, password, system_role, business_role)
        VALUES (?, ?, ?, ?)
    ''', (username, details["password"], details["role"], details["job"]))

conn.commit()
conn.close()