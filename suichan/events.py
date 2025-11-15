"""Event management and validation."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional, Sequence
import json
import logging
import sqlite3
import uuid
import re

from .config import AppConfig
from .db import Database

LOGGER = logging.getLogger(__name__)

RECOMMENDED_MIN = -5
RECOMMENDED_MAX = 5
HIGHLIGHT_THRESHOLD = 10


@dataclass
class Event:
    id: str
    timestamp: datetime
    category_id: str
    point: int
    note: Optional[str]
    extra: Optional[Dict[str, Any]]


class PointValidationError(ValueError):
    """Raised when point validation fails."""


class ExtraValidationError(ValueError):
    """Raised when the extra payload is invalid."""


class EventService:
    def __init__(self, database: Database, config: AppConfig) -> None:
        self.database = database
        self.config = config

    def record(
        self,
        category_id: str,
        point: int = 1,
        note: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ) -> Event:
        point = self._validate_point(point)
        timestamp_utc = timestamp or datetime.now(tz=UTC)
        extra_payload = self._validate_extra(extra)

        with self.database.connect() as conn:
            event_id = str(uuid.uuid4())
            conn.execute(
                """
                INSERT INTO events (id, timestamp, category_id, point, note, extra)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    int(timestamp_utc.timestamp()),
                    category_id,
                    point,
                    note,
                    json.dumps(extra_payload) if extra_payload else None,
                ),
            )
            conn.commit()

        return Event(
            id=event_id,
            timestamp=timestamp_utc.astimezone(self.config.timezone),
            category_id=category_id,
            point=point,
            note=note,
            extra=extra_payload,
        )

    def list(self, limit: Optional[int] = None) -> List[Event]:
        query = "SELECT * FROM events ORDER BY timestamp DESC"
        params: Sequence[object] = ()
        if limit is not None:
            query += " LIMIT ?"
            params = (limit,)

        with self.database.connect() as conn:
            cur = conn.execute(query, params)
            rows = cur.fetchall()

        events: List[Event] = []
        for row in rows:
            events.append(self._row_to_event(row))
        return events

    def _validate_point(self, point: int) -> int:
        if not isinstance(point, int):
            raise PointValidationError("Point must be an integer")
        if point < RECOMMENDED_MIN or point > RECOMMENDED_MAX:
            LOGGER.info(
                "Point %s outside recommended range (%s..%s)",
                point,
                RECOMMENDED_MIN,
                RECOMMENDED_MAX,
            )
        return point

    def _validate_extra(
        self, extra: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        if extra is None:
            return None
        if not isinstance(extra, dict):
            raise ExtraValidationError("extra must be a dictionary when provided")
        snake_case = re.compile(r"^[a-z0-9_]+$")
        sanitized: Dict[str, Any] = {}
        for key, value in extra.items():
            if not isinstance(key, str) or not snake_case.match(key):
                raise ExtraValidationError(
                    "extra keys must be snake_case strings: %s" % key
                )
            sanitized[key] = value
        return sanitized

    def _row_to_event(self, row: sqlite3.Row) -> Event:
        timestamp_utc = datetime.fromtimestamp(int(row["timestamp"]), tz=UTC)
        timestamp_local = timestamp_utc.astimezone(self.config.timezone)
        extra: Optional[dict] = None
        if row["extra"]:
            try:
                loaded = json.loads(row["extra"])
                extra = self._validate_extra(loaded)
            except (json.JSONDecodeError, ExtraValidationError):
                LOGGER.warning("Invalid JSON in extra for event %s", row["id"])
        return Event(
            id=row["id"],
            timestamp=timestamp_local,
            category_id=row["category_id"],
            point=int(row["point"]),
            note=row["note"],
            extra=extra,
        )

    def highlight_required(self, point: int) -> bool:
        return abs(point) >= HIGHLIGHT_THRESHOLD

    def recommended_range(self) -> tuple[int, int]:
        return (RECOMMENDED_MIN, RECOMMENDED_MAX)
