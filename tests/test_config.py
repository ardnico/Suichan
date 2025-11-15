from pathlib import Path

from suichan.config import load_config


def test_load_config_with_override(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text('{"timezone_override": "Asia/Tokyo"}', encoding="utf-8")

    config = load_config(config_path)

    assert config.timezone.key == "Asia/Tokyo"


def test_load_config_missing_file(tmp_path):
    config = load_config(tmp_path / "missing.json")
    assert config.timezone is not None
