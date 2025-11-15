"""Category management."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional
import logging
import sqlite3
import uuid

from .db import Database

LOGGER = logging.getLogger(__name__)


@dataclass
class Category:
    id: str
    label: str
    color: str
    archived: bool
    sort_order: int


DEFAULT_CATEGORIES: Iterable[tuple[str, str]] = (
    ("いたずら", "#f7a072"),
    ("かわいい", "#f28482"),
    ("ほめたい", "#84a59d"),
    ("すごい", "#81b29a"),
    ("にこが嬉しかった", "#e0aaff"),
    ("にこが困った", "#f6bd60"),
)


class CategoryService:
    def __init__(self, database: Database) -> None:
        self.database = database
        self._ensure_defaults()

    def _ensure_defaults(self) -> None:
        with self.database.connect() as conn:
            cur = conn.execute("SELECT COUNT(*) FROM categories")
            (count,) = cur.fetchone()
            if count:
                return
            LOGGER.info("Seeding default categories")
            for order, (label, color) in enumerate(DEFAULT_CATEGORIES):
                self._insert_category(conn, label, color, order)
            conn.commit()

    def create(self, label: str, color: str) -> Category:
        with self.database.connect() as conn:
            order = self._next_sort_order(conn)
            row = self._insert_category(conn, label, color, order)
            conn.commit()
            return row

    def list(self, include_archived: bool = False) -> List[Category]:
        query = "SELECT * FROM categories"
        params: tuple[object, ...] = ()
        if not include_archived:
            query += " WHERE archived = 0"
        query += " ORDER BY sort_order"
        with self.database.connect() as conn:
            cur = conn.execute(query, params)
            return [self._row_to_category(row) for row in cur.fetchall()]

    def archive(self, category_id: str, archived: bool = True) -> None:
        with self.database.connect() as conn:
            conn.execute(
                "UPDATE categories SET archived = ? WHERE id = ?",
                (1 if archived else 0, category_id),
            )
            conn.commit()

    def reorder(self, category_id: str, new_order: int) -> None:
        with self.database.connect() as conn:
            cur = conn.execute(
                "SELECT id FROM categories ORDER BY sort_order, label"
            )
            category_ids = [row["id"] for row in cur.fetchall()]
            if category_id not in category_ids:
                raise ValueError(f"Unknown category {category_id}")
            category_ids.remove(category_id)
            new_order = max(0, min(new_order, len(category_ids)))
            category_ids.insert(new_order, category_id)
            for order, cid in enumerate(category_ids):
                conn.execute(
                    "UPDATE categories SET sort_order = ? WHERE id = ?",
                    (order, cid),
                )
            conn.commit()

    def merge(self, source_id: str, target_id: str) -> None:
        if source_id == target_id:
            return
        with self.database.connect() as conn:
            conn.execute(
                "UPDATE events SET category_id = ? WHERE category_id = ?",
                (target_id, source_id),
            )
            conn.execute("DELETE FROM categories WHERE id = ?", (source_id,))
            self._normalize_sort_order(conn)
            conn.commit()

    def get(self, category_id: str) -> Optional[Category]:
        with self.database.connect() as conn:
            cur = conn.execute("SELECT * FROM categories WHERE id = ?", (category_id,))
            row = cur.fetchone()
            return self._row_to_category(row) if row else None

    def _normalize_sort_order(self, conn: sqlite3.Connection) -> None:
        cur = conn.execute(
            "SELECT id FROM categories ORDER BY sort_order, label"
        )
        for order, (category_id,) in enumerate(cur.fetchall()):
            conn.execute(
                "UPDATE categories SET sort_order = ? WHERE id = ?",
                (order, category_id),
            )

    def _next_sort_order(self, conn: sqlite3.Connection) -> int:
        cur = conn.execute("SELECT COALESCE(MAX(sort_order), -1) FROM categories")
        (value,) = cur.fetchone()
        return int(value) + 1

    def _insert_category(
        self, conn: sqlite3.Connection, label: str, color: str, order: int
    ) -> Category:
        category_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO categories (id, label, color, archived, sort_order) VALUES (?, ?, ?, 0, ?)",
            (category_id, label, color, order),
        )
        return Category(
            id=category_id,
            label=label,
            color=color,
            archived=False,
            sort_order=order,
        )

    def _row_to_category(self, row: sqlite3.Row) -> Category:
        return Category(
            id=row["id"],
            label=row["label"],
            color=row["color"],
            archived=bool(row["archived"]),
            sort_order=int(row["sort_order"]),
        )
