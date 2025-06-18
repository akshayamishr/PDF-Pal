import sqlite3
import json
from datetime import datetime
from google.genai import types

DATABASE_FILE = 'chatbot_conversations.db'

def init_db():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT NOT NULL,
            role TEXT NOT NULL, -- 'user' or 'model'
            content TEXT NOT NULL, -- The message content (serialized JSON)
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_message(chat_id: str, role: str, message: str):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO chat_messages (chat_id, role, content) VALUES (?, ?, ?)",
        (chat_id, role, message)
    )
    conn.commit()
    conn.close()

def load_chat_history(chat_id: str):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT role, content FROM chat_messages WHERE chat_id = ? ORDER BY timestamp",
        (chat_id,)
    )
    rows = cursor.fetchall()
    conn.close()

    history = []
    for role, msg in rows:
        try:
            history.append(types.Content(
            role=role, 
            parts=[types.Part(text = msg)]))
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON for chat_id {chat_id}, content: {msg}. Error: {e}")
            continue # Skip corrupted messages
    return history


init_db()
