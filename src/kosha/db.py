import sqlite3
import os
import datetime
import json
import pytz

DB_NAME = 'database.db'
 
def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS users
                (id INTEGER PRIMARY KEY, -- Auto-incrementing primary key (internal user ID)
            telegram_chat_id INTEGER UNIQUE NOT NULL   -- Telegram's chat ID
                    
                   
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
                timestamp TEXT NOT NULL, -- when to send the reminder
                is_active BOOLEAN DEFAULT TRUE,-- whether the reminder is active
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE -- Foreign key constraint
                );''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS summaries
                (id INTEGER PRIMARY KEY, -- Auto-incrementing primary key (internal summary ID)
                user_id INTEGER NOT NULL, -- Foreign key referencing the user table
                content TEXT NOT NULL, -- The content of the summary
                date DATE NOT NULL, -- The date of the summary
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, -- The timestamp of the summary
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE, -- Foreign key constraint
                UNIQUE(user_id, date) -- Ensure there's only one summary per user and date
                   
                );''')
    # creating todo table. Should have is_active column to track if task is done or not
    cursor.execute('''CREATE TABLE IF NOT EXISTS todo
                (id INTEGER PRIMARY KEY, -- Auto-incrementing primary key (internal todo ID)
                user_id INTEGER NOT NULL, -- Foreign key referencing the user table 
                content TEXT NOT NULL, -- The content of the todo item
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, -- The timestamp of the last todo update
                is_done BOOLEAN DEFAULT FALSE,-- whether the todo was completed
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE  -- Foreign key constraint
                );''')

 #   cursor.execute('''CREATE TABLE IF NOT EXISTS sleep
 #               (id INTEGER PRIMARY KEY, -- Auto-incrementing primary key (internal sleep log ID)
 #               user_id INTEGER NOT NULL, -- Foreign key referencing the user table
#                date  DATE NOT NULL, -- The date of the sleep session   
 #               sleep_start DATETIME NOT NULL, -- The start time of the sleep session
 #               sleep_end DATETIME DEFAULT NULL, -- The end time of the sleep session
 #               sleep_duration TEXT DEFAULT NULL, -- The duration of the sleep session
 #               FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE -- Foreign key constraint
 #               );''')

    
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

def get_active_reminders( ):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT r.id, u.telegram_chat_id AS chat_id, r.content, r.timestamp
        FROM reminders r
        JOIN users u ON r.user_id = u.id
        WHERE r.is_active = TRUE
        ORDER BY r.timestamp
    """)
    active_reminders = cursor.fetchall()

    conn.close()

    return active_reminders 

def add_summary(user_id, content, date):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO summaries (user_id, content, date) VALUES (?, ?, ?)", (user_id, content, date.isoformat()))
        conn.commit()
        print(f"Summary added for user ID: {user_id}")
    except sqlite3.IntegrityError:
        print(f"Summary already exists for user ID: {user_id}")
        conn.rollback()
    finally:

        conn.close()

    

def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor() 

    cursor.execute("SELECT id, telegram_chat_id FROM users")
    users = cursor.fetchall()

    conn.close() 

    return users   

def get_summary_for_user(user_id, date):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT content FROM summaries WHERE user_id = ? AND date = ?", (user_id, date.isoformat()))
    summary = cursor.fetchone()

    conn.close()

    return summary

def add_todo(user_id, content):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    cursor.execute("INSERT INTO todo (user_id, content) VALUES (?, ?)", (user_id, content))
    todo_id = cursor.lastrowid
    conn.commit()
    conn.close() 
    return todo_id

    

def get_todos_for_user(user_id,date): 
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT  id, content, is_done FROM todo WHERE user_id = ? AND DATE(timestamp) = ? ORDER BY timestamp ", (user_id,date))
    todos = cursor.fetchall()

    conn.close()

    return todos

def mark_todo_done(todo_id,new_value):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    cursor.execute("UPDATE todo SET is_done = ? WHERE id = ?", (new_value, todo_id))
    conn.commit()

    conn.close()

    print(f"Todo {todo_id} marked as done.")
    return new_value

def delete_todo(todo_id):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM todo WHERE id = ?", (todo_id,))
    conn.commit()

    conn.close()

    print(f"Todo {todo_id} deleted.")

'''def log_sleep_start(user_id,timestamp):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    cursor.execute("INSERT INTO sleep (user_id, start_time) VALUES (?, ?)", (user_id, timestamp.isoformat()))
    id = cursor.lastrowid
    cursor.execute("UPDATE sleep SET date = DATE(start_time) WHERE id = ?", (id,))
     
    conn.commit()

    conn.close()

def log_sleep_end(sleep_id, timestamp):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    cursor.execute("UPDATE sleep SET end_time = ? WHERE id = ?", (timestamp.isoformat(), sleep_id))
    cursor.execute("UPDATE sleep SET duration = end_time - start_time WHERE id = ?", (sleep_id,))
 
    conn.commit()

    conn.close()

    print(f"Sleep {sleep_id} logged.")

def get_sleeps_where_not_ended(user_id):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    #fetch not ended sleeps for last three days
    cursor.execute("SELECT * FROM sleep WHERE user_id = ? AND end_time IS NULL ORDER BY start_time DESC LIMIT 3", (user_id,))
    
    sleeps = cursor.fetchall ()

    conn.close()

    return sleeps

def get_sleeplogs_for_day(user_id,date):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM sleep WHERE user_id = ? AND DATE(start_time) = ? ORDER BY start_time ", (user_id,date.isoformat()))
    sleeps = cursor.fetchall()

    conn.close()

    return sleeps'''