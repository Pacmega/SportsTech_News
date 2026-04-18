# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SportsTech_News is a Python bot that fetches sports technology news from RSS feeds and sends daily briefs via Telegram. It runs on a cron schedule via GitHub Actions (daily at 10:00 AM UTC).

## Commands

```bash
# Run the bot locally
uv run python -m src.main

# Install dependencies
uv sync                   # runtime only
uv sync --group dev       # with dev tools

# Tests
uv run pytest                          # all tests with coverage
uv run pytest tests/test_scraper.py    # single test file
uv run pytest -k "test_is_recent"      # single test by name

# Code quality
uv run black src/ tests/               # format
uv run ruff check src/ tests/ --fix    # lint
uv run mypy src/                       # type check
```

Environment variables are required to run locally — copy `.env.example` to `.env` and fill in `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`.

## Architecture

Three-layer pipeline: **scraper → main → telegram bot**

- `src/scraper.py` — fetches and filters RSS feeds. `NewsScraper` holds a dict of feeds (`RSS_FEEDS`) and a `HOURS_LOOKBACK` (default 25h). `get_all_news()` returns `NewsArticle` dataclasses sorted newest-first. Both classes use context managers for resource cleanup.
- `src/main.py` — orchestrates: fetch → format → send. Entry point for the GitHub Actions job.
- `src/telegram_bot.py` — formats articles as HTML and posts to Telegram via Bot API. `TelegramBot` reads credentials from env vars at init.

**Adding a new RSS feed**: add an entry to the `RSS_FEEDS` dict in `src/scraper.py` — no other changes needed.

## Tooling

- **Package manager**: `uv` (not pip). Use `uv run` to execute scripts within the venv.
- **Formatter**: Black, 100-char line length.
- **Linter**: Ruff, checks `E`, `F`, `I`, `W`.
- **Type checker**: MyPy with `check_untyped_defs = true`, Python 3.12.
- **Tests**: Pytest; coverage is on by default (`--cov=src --cov-report=term-missing` in `pyproject.toml`).

## Deployment

GitHub Actions workflow (`.github/workflows/daily_brief.yml`) runs the bot. Secrets `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` must be set in the repo's Actions secrets. Manual runs are available via `workflow_dispatch`.
