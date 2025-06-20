import sqlite3
import os
import datetime

DB_NAME = 'database.db'
 
def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS users
                (id INTEGER PRIMARY KEY, -- Auto-incrementing primary key (internal user ID)
            telegram_chat_id INTEGER UNIQUE NOT NULL  -- Telegram's chat ID
            -- We'll add daily_summary_time and other settings here later
            );''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS logs
                (id INTEGER PRIMARY KEY, -- Auto-incrementing primary key (internal message ID)
                user_id INTEGER NOT NULL, -- Foreign key referencing the user table
                content TEXT NOT NULL, -- The content of the message
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, -- The timestamp of the message
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE -- Foreign key constraint
                );''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS reminders
                (id INTEGER PRIMARY KEY, -- Auto-incrementing primary key (internal reminder ID)
                user_id INTEGER NOT NULL, -- Foreign key referencing the user table
                content TEXT NOT NULL, -- The content of the reminder
                timestamp DATETIME NOT NULL, -- when to send the reminder
                is_active BOOLEAN DEFAULT TRUE,-- whether the reminder is active
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE -- Foreign key constraint
                );''')

    conn.commit()
    conn.close()

    print("Database initialized.")

def get_or_create_user(telegram_chat_id):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE telegram_chat_id = ?", (telegram_chat_id,))
    user = cursor.fetchone()

    if user:
        user_id = user[0]
    else:
        cursor.execute("INSERT INTO users (telegram_chat_id) VALUES (?)", (telegram_chat_id,))
        conn.commit()
        user_id = cursor.lastrowid
        print(f"New user created with ID: {user_id} (chat ID: {telegram_chat_id})")

    conn.close()

    return user_id

def log_message(user_id,content):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    cursor.execute("INSERT INTO logs (user_id, content) VALUES (?, ?)", (user_id, content))
    conn.commit()

    conn.close()

    print(f"Message logged for user ID: {user_id}")

def get_messages_for_day(user_id,date):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    cursor.execute("SELECT timestamp,content FROM logs WHERE user_id = ? AND DATE(timestamp) = ? ORDER BY timestamp ", (user_id,date))
    logs = cursor.fetchall()

    conn.close()

    return logs

def set_reminder(user_id, content, timestamp):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    cursor.execute("INSERT INTO reminders (user_id, content, timestamp, is_active) VALUES (?, ?, ?, ?)", (user_id, content, timestamp.isoformat(), True))
    conn.commit()
    reminder_id = cursor.lastrowid

    conn.close()

    print(f"Reminder {reminder_id} set for user ID: {user_id}")
    return reminder_id

def deactivate_reminder(reminder_id):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    cursor.execute("UPDATE reminders SET is_active = FALSE WHERE id = ?", (reminder_id,))
    conn.commit()

    conn.close()

    print(f"Reminder {reminder_id} deactivated.")

'''def get_active_reminders(user_id):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    cursor.execute("SELECT id, content, timestamp FROM reminders WHERE user_id = ? AND is_active = TRUE", (user_id,))
    active_reminders = cursor.fetchall()

    conn.close()

    return active_reminders'''