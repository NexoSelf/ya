import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_ids: frozenset[int]
    db_path: str


def load_settings() -> Settings:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("BOT_TOKEN تنظیم نشده است.")
    raw = os.getenv("ADMIN_IDS", "").strip()
    ids = frozenset(int(x.strip()) for x in raw.split(",") if x.strip().isdigit())
    db = os.getenv("DB_PATH", "data/ya.sqlite3").strip() or "data/ya.sqlite3"
    return Settings(token, ids, db)
