import sqlite3
from pathlib import Path

DB = Path("data.db")

def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    c = conn()
    c.execute("""
      CREATE TABLE IF NOT EXISTS api_keys (
        telegram_id INTEGER PRIMARY KEY,
        provider TEXT NOT NULL,
        encrypted_key TEXT NOT NULL,
        last4 TEXT NOT NULL,
        active INTEGER NOT NULL DEFAULT 1
      )
    """)
    c.execute("""
      CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER NOT NULL,
        prompt TEXT NOT NULL,
        result TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    """)
    c.commit()
    c.close()

def save_key(telegram_id, provider, encrypted_key, last4):
    c = conn()
    c.execute("""INSERT INTO api_keys(telegram_id,provider,encrypted_key,last4,active)
                 VALUES(?,?,?,?,1)
                 ON CONFLICT(telegram_id) DO UPDATE SET
                 provider=excluded.provider,
                 encrypted_key=excluded.encrypted_key,
                 last4=excluded.last4,
                 active=1""",
              (telegram_id, provider, encrypted_key, last4))
    c.commit(); c.close()

def get_key(telegram_id):
    c = conn()
    row = c.execute("SELECT * FROM api_keys WHERE telegram_id=? AND active=1", (telegram_id,)).fetchone()
    c.close()
    return dict(row) if row else None

def get_key_info(telegram_id):
    row = get_key(telegram_id)
    return row

def delete_key(telegram_id):
    c = conn()
    c.execute("UPDATE api_keys SET active=0 WHERE telegram_id=?", (telegram_id,))
    c.commit(); c.close()

def save_project(telegram_id, prompt, result):
    c = conn()
    c.execute("INSERT INTO projects(telegram_id,prompt,result) VALUES(?,?,?)",
              (telegram_id, prompt, result))
    c.commit(); c.close()
