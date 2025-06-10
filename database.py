import aiosqlite
import os

DB_NAME = "users.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                gender TEXT,
                notification_time TEXT,
                notification_freq TEXT
            )
        """)
        await db.commit()

async def add_or_update_user(telegram_id, username, gender, notification_time, notification_freq):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT INTO users (telegram_id, username, gender, notification_time, notification_freq)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                username = excluded.username,
                gender = excluded.gender,
                notification_time = excluded.notification_time,
                notification_freq = excluded.notification_freq
        """, (telegram_id, username, gender, notification_time, notification_freq))
        await db.commit()

async def get_user(telegram_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,)) as cursor:
            return await cursor.fetchone()

async def get_users():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT * FROM users") as cursor:
            return await cursor.fetchall()
        

