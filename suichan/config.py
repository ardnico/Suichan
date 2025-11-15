"""Application configuration helpers."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import json
import logging

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

LOGGER = logging.getLogger(__name__)


@dataclass
class AppConfig:
    """Runtime configuration for the application."""

    timezone: ZoneInfo
    raw: Dict[str, Any]


DEFAULT_TIMEZONE = "UTC"
CONFIG_FILENAME = "config.json"


def load_config(path: Optional[Path] = None) -> AppConfig:
    """Load configuration from JSON file.

    The file is optional. If the file or timezone are not provided, fall back to
    the system local timezone and, if that cannot be determined, UTC.
    """

    if path is None:
        path = Path(CONFIG_FILENAME)

    data: Dict[str, Any] = {}
    if path.exists():
        try:
            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except json.JSONDecodeError as exc:
            LOGGER.warning("Failed to parse config %s: %s", path, exc)
            data = {}
    tz_name = data.get("timezone_override")

    timezone = _resolve_timezone(tz_name)

    return AppConfig(timezone=timezone, raw=data)


def _resolve_timezone(tz_name: Optional[str]) -> ZoneInfo:
    if tz_name:
        try:
            return ZoneInfo(tz_name)
        except ZoneInfoNotFoundError:
            LOGGER.warning("Unknown timezone override '%s', falling back", tz_name)

    try:
        local_tz = datetime.now().astimezone().tzinfo
        if isinstance(local_tz, ZoneInfo):
            return local_tz
    except Exception:
        LOGGER.debug("Unable to determine system timezone; using UTC")

    return ZoneInfo(DEFAULT_TIMEZONE)
