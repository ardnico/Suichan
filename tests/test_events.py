from datetime import UTC, datetime

import pytest

from suichan.categories import CategoryService
from suichan.config import AppConfig
from suichan.db import Database
from suichan.events import EventService, ExtraValidationError, PointValidationError


def make_services(tmp_path):
    db = Database(tmp_path / "events.db")
    categories = CategoryService(db)
    config = AppConfig(timezone=UTC, raw={})
    events = EventService(db, config)
    return categories, events


def test_record_and_list_events(tmp_path):
    categories, events = make_services(tmp_path)
    category = categories.list()[0]

    recorded = events.record(
        category.id,
        point=3,
        note="テスト",
        extra={"extra_version": 1, "photo_path": "/tmp/test.jpg"},
        timestamp=datetime(2024, 1, 1, tzinfo=UTC),
    )

    assert recorded.point == 3
    assert recorded.extra["extra_version"] == 1

    retrieved = events.list()
    assert len(retrieved) == 1
    assert retrieved[0].note == "テスト"
    assert retrieved[0].extra["photo_path"] == "/tmp/test.jpg"


def test_point_validation_requires_integer(tmp_path):
    categories, events = make_services(tmp_path)
    category = categories.list()[0]

    with pytest.raises(PointValidationError):
        events.record(category.id, point=3.5)


def test_extra_requires_snake_case(tmp_path):
    categories, events = make_services(tmp_path)
    category = categories.list()[0]

    with pytest.raises(ExtraValidationError):
        events.record(category.id, extra={"BadKey": True})
