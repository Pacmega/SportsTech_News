# Quick Start Guide

## Local Development Setup

### 1. Install uv (if not already installed)

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (with PowerShell)
powershell -ExecutionPolicy BypassUser -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Verify installation:
```bash
uv --version
```

### 2. Clone and Setup Project

```bash
cd ~/Documents/Projects/SportsTech_News
uv sync
```

### 3. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your Telegram credentials
```

### 4. Run Locally

```bash
# Run the bot once
uv run python -m src.main

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=src
```

## GitHub Actions Deployment

### 1. Add Repository Secrets

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Add two new secrets:
   - `TELEGRAM_BOT_TOKEN`: Your bot token from @BotFather
   - `TELEGRAM_CHAT_ID`: Your Telegram chat ID

**Finding your Chat ID:**
```bash
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates"
```

### 2. Verify Workflow

1. Go to **Actions** tab in your repository
2. Select "Daily Sports Tech News Brief" workflow
3. Click **Run workflow** to test manually
4. Check logs to verify successful execution

### 3. Schedule Configuration

The workflow runs daily at 9:00 AM UTC. To change:

Edit `.github/workflows/daily_brief.yml` and modify:
```yaml
schedule:
  - cron: "0 9 * * *"  # Change the numbers as needed
```

**Cron format**: `minute hour day month day_of_week`
- `0 9 * * *` = Every day at 9:00 AM UTC
- `0 8 * * MON` = Every Monday at 8:00 AM UTC
- `*/30 * * * *` = Every 30 minutes

## Adding News Sources

### Option 1: NewsAPI Integration

```python
# In src/scraper.py
def fetch_from_newsapi(self, api_key: str) -> list[NewsArticle]:
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": "sports technology",
        "sortBy": "publishedAt",
        "apiKey": api_key
    }
    response = self.client.get(url, params=params)
    # Parse JSON response...
```

### Option 2: RSS Feed

```python
import feedparser

def fetch_from_rss(self, feed_url: str) -> list[NewsArticle]:
    feed = feedparser.parse(feed_url)
    articles = []
    for entry in feed.entries[:10]:
        articles.append(NewsArticle(
            title=entry.title,
            url=entry.link,
            summary=entry.summary,
            published_at=entry.published
        ))
    return articles
```

### Option 3: Custom Web Scraper

Already implemented in `scraper.py`. Update the HTML selectors for your target website.

## Troubleshooting

### "ModuleNotFoundError: No module named 'src'"

```bash
# Make sure you're using uv run
uv run python -m src.main

# Or add src to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python -m src.main
```

### "ValueError: TELEGRAM_BOT_TOKEN is required"

1. Check `.env` file exists and has correct values
2. If using GitHub Actions, verify secrets are added in Settings
3. Test the token manually:
   ```bash
   curl "https://api.telegram.org/bot<YOUR_TOKEN>/getMe"
   ```

### Workflow runs but bot doesn't send messages

1. Check GitHub Actions logs for errors
2. Verify chat ID is correct (should be numeric)
3. Ensure bot can access Telegram API (networking issues)
4. Check bot doesn't have restricted permissions

### No articles found

1. Verify scraper URLs are accessible
2. Check HTML structure hasn't changed
3. Try using NewsAPI or RSS feeds instead
4. Add debug logging to `src/scraper.py`

## Development Workflow

### Running Code Quality Checks

```bash
# Format code
uv run black src/ tests/

# Lint
uv run ruff check src/ tests/ --fix

# Type check
uv run mypy src/

# All together
uv run black src/ tests/ && \
uv run ruff check src/ tests/ --fix && \
uv run mypy src/ && \
uv run pytest
```

### Pre-commit Hook (Optional)

Create `.git/hooks/pre-commit`:
```bash
#!/bin/bash
uv run black src/ tests/
uv run ruff check src/ tests/ --fix
uv run mypy src/
```

Make it executable:
```bash
chmod +x .git/hooks/pre-commit
```

## Production Considerations

- **Error Handling**: Add retries with exponential backoff for API calls
- **Rate Limiting**: Implement request throttling if scraping multiple sources
- **Logging**: Monitor logs in GitHub Actions for failures
- **Monitoring**: Consider adding health checks or status webhooks
- **News Sources**: Rotate sources or use multiple APIs for redundancy

## Support & Documentation

- [uv Documentation](https://docs.astral.sh/uv/)
- [httpx Documentation](https://www.python-httpx.org/)
- [telegram Bot API](https://core.telegram.org/bots/api)
- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/)
