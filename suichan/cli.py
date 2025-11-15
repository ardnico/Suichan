"""Command line interface for Mount Suichan."""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from .categories import CategoryService
from .config import load_config
from .db import Database
from .events import EventService, ExtraValidationError, PointValidationError

LOGGER = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mount Suichan event recorder")
    parser.add_argument(
        "--database", type=Path, default=None, help="Path to the SQLite database file"
    )
    parser.add_argument(
        "--config", type=Path, default=None, help="Path to the configuration file"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list-categories", help="List available categories")

    add_category = subparsers.add_parser("add-category", help="Create a new category")
    add_category.add_argument("label")
    add_category.add_argument("color")

    archive = subparsers.add_parser("archive-category", help="Archive or restore a category")
    archive.add_argument("category_id")
    archive.add_argument(
        "--restore",
        action="store_true",
        help="Restore the category instead of archiving",
    )

    reorder = subparsers.add_parser("reorder-category", help="Update category order")
    reorder.add_argument("category_id")
    reorder.add_argument("order", type=int)

    merge = subparsers.add_parser("merge-categories", help="Merge two categories")
    merge.add_argument("source_id")
    merge.add_argument("target_id")

    record = subparsers.add_parser("record-event", help="Record a new event")
    record.add_argument("category_id")
    record.add_argument("point", type=int, nargs="?", default=1)
    record.add_argument("--note", default=None)
    record.add_argument("--extra", help="JSON string for the extra payload")

    list_events = subparsers.add_parser("list-events", help="List recent events")
    list_events.add_argument("--limit", type=int)

    return parser


def run_cli(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        filename="debug.log",
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    config = load_config(args.config)
    database = Database(args.database)
    categories = CategoryService(database)
    events = EventService(database, config)

    if args.command == "list-categories":
        return _list_categories(categories)
    if args.command == "add-category":
        category = categories.create(args.label, args.color)
        print(f"Created category {category.label} ({category.id})")
        return 0
    if args.command == "archive-category":
        categories.archive(args.category_id, archived=not args.restore)
        action = "Restored" if args.restore else "Archived"
        print(f"{action} {args.category_id}")
        return 0
    if args.command == "reorder-category":
        categories.reorder(args.category_id, args.order)
        print(f"Updated order for {args.category_id} -> {args.order}")
        return 0
    if args.command == "merge-categories":
        categories.merge(args.source_id, args.target_id)
        print(f"Merged {args.source_id} into {args.target_id}")
        return 0
    if args.command == "record-event":
        try:
            extra_payload = _parse_extra(args.extra)
        except argparse.ArgumentTypeError as exc:
            parser.error(str(exc))
        try:
            event = events.record(
                args.category_id,
                point=args.point,
                note=args.note,
                extra=extra_payload,
            )
        except (PointValidationError, ExtraValidationError) as exc:
            parser.error(str(exc))
        highlight = " !!!" if events.highlight_required(event.point) else ""
        print(
            f"Recorded event {event.id} at {event.timestamp:%Y-%m-%d %H:%M:%S}"
            f" point={event.point}{highlight}"
        )
        return 0
    if args.command == "list-events":
        for event in events.list(limit=args.limit):
            highlight = " !!!" if events.highlight_required(event.point) else ""
            note = f" note={event.note}" if event.note else ""
            extra = f" extra={json.dumps(event.extra)}" if event.extra else ""
            print(
                f"{event.timestamp:%Y-%m-%d %H:%M:%S} category={event.category_id}"
                f" point={event.point}{highlight}{note}{extra}"
            )
        return 0

    parser.error("Unknown command")
    return 1


def _list_categories(service: CategoryService) -> int:
    categories = service.list(include_archived=True)
    for category in categories:
        status = "archived" if category.archived else "active"
        print(
            f"{category.sort_order:02d} {category.label} ({category.id}) color={category.color} {status}"
        )
    return 0


def _parse_extra(raw: Optional[str]) -> Optional[Dict[str, Any]]:
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"Invalid JSON for extra: {exc}") from exc
    if not isinstance(data, dict):
        raise argparse.ArgumentTypeError("extra must decode to a JSON object")
    return data


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(run_cli())
