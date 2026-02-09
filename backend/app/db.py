from __future__ import annotations

from sqlalchemy import text
from sqlmodel import SQLModel, Session, create_engine

from app.config import settings


engine = create_engine(settings.truecheck_db_url, echo=False)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)

    # Lightweight SQLite migration for dev: add new columns if the DB already exists.
    # (SQLModel won't ALTER existing tables automatically.)
    if engine.url.get_backend_name() == "sqlite":
        with engine.begin() as conn:
            try:
                rows = conn.execute(text("PRAGMA table_info(claim)"))
                existing = {r[1] for r in rows}  # (cid, name, type, ...)
                if "rationale" not in existing:
                    conn.execute(text("ALTER TABLE claim ADD COLUMN rationale TEXT"))
                if "reasoning_json" not in existing:
                    conn.execute(text("ALTER TABLE claim ADD COLUMN reasoning_json TEXT"))
            except Exception:
                # If PRAGMA fails for any reason, don't block startup.
                return


def get_session() -> Session:
    return Session(engine)
