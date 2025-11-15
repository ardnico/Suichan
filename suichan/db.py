"""Database utilities for Mount Suichan."""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Iterable, Optional
import logging
import sqlite3

LOGGER = logging.getLogger(__name__)

DB_FILENAME = "suichan.db"

INIT_STATEMENTS: Iterable[str] = (
    """
    CREATE TABLE IF NOT EXISTS categories (
        id TEXT PRIMARY KEY,
        label TEXT NOT NULL,
        color TEXT NOT NULL,
        archived INTEGER NOT NULL DEFAULT 0,
        sort_order INTEGER NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS events (
        id TEXT PRIMARY KEY,
        timestamp INTEGER NOT NULL,
        category_id TEXT NOT NULL,
        point INTEGER NOT NULL,
        note TEXT,
        extra TEXT,
        FOREIGN KEY(category_id) REFERENCES categories(id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_events_category ON events(category_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)
    """,
)


class Database:
    """Lightweight wrapper around sqlite3 with schema management."""

    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = Path(path or DB_FILENAME)
        self._ensure_directory()
        LOGGER.debug("Using database at %s", self.path)
        self._initialize()

    def _ensure_directory(self) -> None:
        if self.path.parent and not self.path.parent.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)

    def _initialize(self) -> None:
        with self._connect() as conn:
            for statement in INIT_STATEMENTS:
                conn.execute(statement)
            conn.commit()

    @contextmanager
    def connect(self) -> Generator[sqlite3.Connection, None, None]:
        with self._connect() as conn:
            yield conn

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
