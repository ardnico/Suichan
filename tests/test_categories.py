from suichan.categories import CategoryService
from suichan.db import Database


def test_default_categories_seeded(tmp_path):
    db = Database(tmp_path / "events.db")
    service = CategoryService(db)

    categories = service.list()

    assert len(categories) == 6
    assert categories[0].sort_order == 0


def test_create_and_reorder_category(tmp_path):
    db = Database(tmp_path / "events.db")
    service = CategoryService(db)

    category = service.create("テスト", "#ffffff")
    service.reorder(category.id, 0)

    updated = service.get(category.id)
    assert updated is not None
    assert updated.sort_order == 0
