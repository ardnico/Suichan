# Mount Suichan – Event Recording System

Mount Suichan is a small Python application that records day-to-day events for Niko and Suichan.
The project follows the design document included in the task description and implements the
initial MVP: event capture, category management, validation, and local persistence backed by
SQLite.

## Project layout

```
.
├── pyproject.toml        # Packaging metadata and dependency declarations
├── README.md             # Project documentation (this file)
├── suichan/              # Application package
│   ├── categories.py     # Category data access and business rules
│   ├── cli.py            # Command line interface for quick entry & browsing
│   ├── config.py         # Config loading (timezone overrides, etc.)
│   ├── db.py             # Database bootstrap utilities
│   └── events.py         # Event validation and persistence helpers
└── tests/                # Pytest-based test suite
```

## Requirements

* Python 3.11 or later (the code relies on `sqlite3` and `zoneinfo` from the standard library)
* `pip` to install the project in editable or regular mode

## Installation

Create and activate a virtual environment using your preferred tool, then install the project
with the optional `dev` dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

The editable installation allows you to run the CLI via the module entry point while you iterate
on the codebase.

## Usage

The CLI provides a handful of subcommands to manage categories and events.  View the available
commands:

```bash
python -m suichan.cli --help
```

The most common workflow is to add an event quickly.  The following command records a
"かわいい" (+3) event with a short note:

```bash
python -m suichan.cli event add \
  --category "かわいい" \
  --point 3 \
  --note "すいちゃんが新しい服を自慢した"
```

Other notable commands:

* `python -m suichan.cli categories list` – show all categories, their colors, and archive state
* `python -m suichan.cli event list` – display stored events grouped by local date
* `python -m suichan.cli categories archive <id>` – hide a category from future entry operations

All commands respect the optional `config.json` file (placed beside your database) for timezone
overrides.

## Testing

The project uses [pytest](https://docs.pytest.org/) for its test suite.  Run the tests locally with:

```bash
pytest
```

## Continuous integration

GitHub Actions is configured to run the test suite on pushes and pull requests.  The workflow file
lives at [`.github/workflows/ci.yml`](.github/workflows/ci.yml) and performs the following steps:

1. Check out the repository
2. Set up Python 3.11
3. Install the project with `pip install .[dev]`
4. Execute `pytest`

This ensures every change that lands on the repository passes the automated tests before merging.

## License

This project is released under the MIT License.  See [LICENSE](LICENSE) for the full text.
