# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`rightprice` is a Python package for determining the right price for properties of interest by scraping sold house data from Right Move. The project is set up as an installable Python package with CLI commands.

## Development Setup

Install using [uv](https://docs.astral.sh/uv/) (recommended):

```bash
uv venv --python 3.13
source .venv/bin/activate
uv pip install -e ".[dev]"  # Install package in editable mode with dev dependencies
```

Install pre-commit hooks:

```bash
pre-commit install
```

## Common Commands

### Running Tests

```bash
pytest                           # Run all tests
pytest tests/test_add_one.py    # Run a specific test file
pytest -v                        # Verbose output
pytest --cov=rightprice         # Run with coverage
```

### Code Quality

```bash
ruff check .                    # Lint code
ruff check --fix .              # Lint and auto-fix
ruff format .                   # Format code
mypy src/                       # Type checking
pre-commit run --all-files      # Run all pre-commit hooks
```

### Documentation

```bash
mkdocs serve                    # Start local docs server
mkdocs build --strict           # Build documentation (errors on warnings)
```

### Building Package

```bash
python -m build                 # Build distribution files
```

### CLI Usage

The package provides a CLI via the `rightprice` command:

```bash
rightprice --help               # Show available commands
rightprice add-one --input-path <file> --output-path <file>  # Example command
```

## Architecture

### Project Structure

- `src/rightprice/`: Main package source
  - `__main__.py`: CLI entry point using Click groups
  - `add_one.py`: Example module showing CLI command pattern
- `scripts/`: Standalone scripts (not part of installable package)
  - `scrape_sold_houses_right_move.py`: Right Move web scraper
- `tests/`: Test files using pytest
- `docs/`: MkDocs documentation source

### CLI Command Pattern

The project uses Click for CLI commands with a group-based structure:

1. Commands are defined as Click commands in their own modules (e.g., `add_one.py`)
2. Commands are registered in `__main__.py` using `cli.add_command()`
3. Entry point `rightprice` is defined in `pyproject.toml` under `[project.scripts]`

To add a new CLI command:
1. Create a new module in `src/rightprice/` with a Click command function
2. Import and register it in `__main__.py` using `cli.add_command()`

### Web Scraping Module

The `scripts/scrape_sold_houses_right_move.py` script scrapes sold property data from Right Move:

- Uses `requests` and `BeautifulSoup` for web scraping
- Uses `tap` (Typed Argument Parser) for CLI arguments
- Implements pagination with delays to avoid rate limiting
- Extracts property type, address, dates, prices, and bedrooms
- Outputs to CSV format using pandas

Key functions:
- `scrape_sold_houses_right_move()`: Main orchestrator, handles pagination
- `get_sold_property_info()`: Parses property cards from a single page
- `extract_dates_prices()`: Extracts date/price pairs from property history

## Code Quality Standards

The project uses:
- **ruff**: Linting and formatting (replaces black, isort, flake8)
- **mypy**: Static type checking
- **pre-commit**: Automated checks on commit including:
  - End of file fixer
  - Trailing whitespace removal
  - YAML validation
  - Large file detection
  - Ruff linting and formatting
  - mypy type checking

All code should have type hints. The project requires Python >= 3.13.

## Testing

Tests use pytest with the following structure:
- `conftest.py`: Shared fixtures and configuration
- `tests/data/`: Test data files
- Test files follow `test_*.py` naming convention

## CI/CD Pipeline

GitHub Actions workflow (`.github/workflows/test_deploy.yml`) handles:

1. **Testing**: Runs `pytest` on all pushes and PRs
2. **Documentation**: Builds and deploys MkDocs to GitHub Pages on main branch pushes
3. **PyPI Publishing**: Builds and publishes package on git tags (releases)

The workflow uses Python 3.13 and custom setup action at `.github/actions/setup/`.
