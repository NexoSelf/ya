from __future__ import annotations
import os
import aiosqlite
from pathlib import Path
from datetime import datetime, timezone

SCHEMA = '''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS chats (
    chat_id INTEGER PRIMARY KEY,
    title TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS scores (
    chat_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    points INTEGER NOT NULL DEFAULT 0,
    wins INTEGER NOT NULL DEFAULT 0,
    truth_count INTEGER NOT NULL DEFAULT 0,
    dare_count INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY(chat_id, user_id)
);
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL,
    kind TEXT NOT NULL CHECK(kind IN ('truth','dare')),
    text TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY(category_id) REFERENCES categories(id)
);
CREATE TABLE IF NOT EXISTS settings (
    chat_id INTEGER NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    PRIMARY KEY(chat_id, key)
);
'''

DEFAULT_CATEGORIES = {
    "عمومی": [("truth", "آخرین چیزی که باعث شد از ته دل بخندی چه بود؟"), ("dare", "با یک ایموجی حال الانت را توضیح بده و دلیلش را بگو.")],
    "دوستانه": [("truth", "اگر بتوانی یک خاطره را دوباره تجربه کنی، کدام را انتخاب می‌کنی؟"), ("dare", "یک جمله تعریف واقعی از نفر سمت راستت بنویس.")],
    "خنده‌دار": [("truth", "عجیب‌ترین کاری که برای خنداندن دوستت کردی چه بود؟"), ("dare", "در یک پیام فقط با سه ایموجی یک داستان بساز.")],
    "چالشی": [("truth", "کدام مهارت را دوست داری امسال یاد بگیری؟"), ("dare", "یک جمله انگیزشی کوتاه برای گروه بنویس.")],
}

def now(): return datetime.now(timezone.utc).isoformat()

class Database:
    def __init__(self, path: str): self.path = path
    async def connect(self):
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        db = await aiosqlite.connect(self.path)
        db.row_factory = aiosqlite.Row
        await db.executescript(SCHEMA)
        for name, qs in DEFAULT_CATEGORIES.items():
            await db.execute("INSERT OR IGNORE INTO categories(name) VALUES(?)", (name,))
            row = await db.execute_fetchone("SELECT id FROM categories WHERE name=?", (name,))
            count = await db.execute_fetchone("SELECT COUNT(*) c FROM questions WHERE category_id=?", (row["id"],))
            if count["c"] == 0:
                await db.executemany("INSERT INTO questions(category_id,kind,text) VALUES(?,?,?)", [(row["id"], k, t) for k,t in qs])
        await db.commit()
        return db
    async def upsert_user(self, u):
        async with await self.connect() as db:
            await db.execute("INSERT INTO users(user_id,username,first_name,created_at) VALUES(?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET username=excluded.username, first_name=excluded.first_name", (u.id,u.username,u.first_name or "کاربر",now()))
            await db.commit()
    async def ensure_score(self, chat_id, user_id):
        async with await self.connect() as db:
            await db.execute("INSERT OR IGNORE INTO scores(chat_id,user_id) VALUES(?,?)", (chat_id,user_id)); await db.commit()
    async def add_points(self, chat_id, user_id, points, win=False, kind=None):
        await self.ensure_score(chat_id,user_id)
        field = "wins" if win else ("truth_count" if kind=="truth" else "dare_count" if kind=="dare" else None)
        async with await self.connect() as db:
            if field: await db.execute(f"UPDATE scores SET points=points+?, {field}={field}+1 WHERE chat_id=? AND user_id=?", (points,chat_id,user_id))
            else: await db.execute("UPDATE scores SET points=points+? WHERE chat_id=? AND user_id=?", (points,chat_id,user_id))
            await db.commit()
    async def score(self, chat_id,user_id):
        await self.ensure_score(chat_id,user_id)
        async with await self.connect() as db: return await db.execute_fetchone("SELECT * FROM scores WHERE chat_id=? AND user_id=?",(chat_id,user_id))
    async def leaderboard(self, chat_id, limit=10):
        async with await self.connect() as db:
            cur=await db.execute("SELECT s.*,u.username,u.first_name FROM scores s LEFT JOIN users u ON u.user_id=s.user_id WHERE s.chat_id=? ORDER BY s.points DESC,s.wins DESC LIMIT ?",(chat_id,limit)); return await cur.fetchall()
    async def categories(self):
        async with await self.connect() as db:
            cur=await db.execute("SELECT * FROM categories ORDER BY id"); return await cur.fetchall()
    async def add_category(self,name):
        async with await self.connect() as db:
            try: await db.execute("INSERT INTO categories(name) VALUES(?)",(name.strip(),)); await db.commit(); return True
            except aiosqlite.IntegrityError: return False
    async def add_question(self,cat_id,kind,text):
        async with await self.connect() as db:
            await db.execute("INSERT INTO questions(category_id,kind,text) VALUES(?,?,?)",(cat_id,kind,text.strip())); await db.commit()
    async def random_question(self,cat_id,kind):
        async with await self.connect() as db:
            return await db.execute_fetchone("SELECT * FROM questions WHERE category_id=? AND kind=? AND active=1 ORDER BY RANDOM() LIMIT 1",(cat_id,kind))
    async def stats(self):
        async with await self.connect() as db:
            a=await db.execute_fetchone("SELECT COUNT(*) c FROM users"); b=await db.execute_fetchone("SELECT COUNT(*) c FROM chats"); c=await db.execute_fetchone("SELECT COUNT(*) c FROM questions WHERE active=1"); return a["c"],b["c"],c["c"]
