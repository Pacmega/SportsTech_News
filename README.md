# Sports Tech News Bot

A Python-based bot that scrapes or fetches sports technology news and sends a daily brief via Telegram.

## Features

- **Modular Architecture**: Clean separation of concerns with distinct modules for scraping, Telegram integration, and main orchestration.
- **Type Hints**: Full type annotations following PEP 8.
- **Environment Variables**: Secure configuration via environment variables for Telegram credentials.
- **Automated Scheduling**: GitHub Actions workflow for daily execution via cron.
- **Extensible**: Placeholder functions for easy integration with APIs (NewsAPI, RSS feeds, custom scrapers).

## Tech Stack

- **Python 3.12+**: Modern Python with improved performance.
- **uv**: Ultra-fast Python package installer and resolver.
- **httpx**: Async-capable HTTP client with intuitive API.
- **beautifulsoup4**: HTML/XML parsing and scraping.
- **python-dotenv**: Environment variable management for local development.

## Project Structure

```
SportsTech_News/
├── .github/
│   └── workflows/
│       └── daily_brief.yml          # GitHub Actions workflow
├── src/
│   ├── __init__.py                  # Package initialization
│   ├── main.py                      # Entry point and orchestration
│   ├── scraper.py                   # News fetching/scraping logic
│   └── telegram_bot.py              # Telegram bot integration
├── tests/                           # Unit tests (create as needed)
├── .env.example                     # Example environment variables
├── pyproject.toml                   # Project configuration and dependencies
└── README.md                        # This file
```

## Setup

### 1. Prerequisites

- Python 3.12 or later
- uv package manager ([install here](https://docs.astral.sh/uv/))
- A Telegram bot token (create via [@BotFather](https://t.me/botfather))
- Your Telegram chat ID

### 2. Local Development

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/sports-tech-news-bot.git
   cd sports-tech-news-bot
   ```

2. **Create `.env` file** (for local testing):
   ```bash
   cp .env.example .env
   # Edit .env with your actual credentials
   ```

3. **Install dependencies**:
   ```bash
   uv sync
   ```

4. **Run the bot**:
   ```bash
   uv run python -m src.main
   ```

### 3. Telegram Setup

1. Create a Telegram bot via [@BotFather](https://t.me/botfather)
2. Get your `TELEGRAM_BOT_TOKEN` from the bot creation message
3. Get your `TELEGRAM_CHAT_ID`:
   - Send a message to your bot
   - Visit `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Find your chat ID in the response

### 4. GitHub Actions Deployment

1. **Add secrets** to your GitHub repository:
   - `TELEGRAM_BOT_TOKEN`: Your bot token
   - `TELEGRAM_CHAT_ID`: Your Telegram chat ID

2. **Workflow triggers**:
   - Automatically runs daily at 9:00 AM UTC (edit `daily_brief.yml` to change schedule)
   - Can also be manually triggered via "Run workflow" in GitHub Actions tab

## Configuration

### Environment Variables

- `TELEGRAM_BOT_TOKEN` (required): Your Telegram bot token
- `TELEGRAM_CHAT_ID` (required): Target Telegram chat ID

### Customization

- **News Sources**: Edit `src/scraper.py` to add custom scrapers or API integrations
- **Schedule**: Modify the cron expression in `.github/workflows/daily_brief.yml`
- **Message Format**: Customize `format_news_brief()` in `src/telegram_bot.py`

## Development

### Code Quality

The project includes configuration for:
- **Black**: Code formatting (100 character line length)
- **Ruff**: Lightning-fast linting
- **MyPy**: Static type checking
- **Pytest**: Unit testing framework

Install dev dependencies:
```bash
uv sync --group dev
```

Run code quality checks:
```bash
# Format code
uv run black src/ tests/

# Lint code
uv run ruff check src/ tests/

# Type check
uv run mypy src/

# Run tests
uv run pytest
```

### Adding News Sources

To integrate additional news sources:

1. Edit `src/scraper.py`
2. Add methods in the `NewsScraper` class following the same pattern
3. Update `get_all_news()` to include new sources
4. Test locally before deploying

Example with NewsAPI:
```python
def fetch_from_newsapi(self, query: str = "sports technology") -> list[NewsArticle]:
    url = "https://newsapi.org/v2/everything"
    params = {"q": query, "sortBy": "publishedAt"}
    # Implementation...
```

## Troubleshooting

### Bot doesn't send messages

1. Verify `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are correct
2. Test bot manually: `https://api.telegram.org/bot<TOKEN>/getMe`
3. Check GitHub Actions logs for error messages

### No articles found

1. Verify scraper URLs are accessible
2. Update HTML selectors in `scraper.py` if website structure changed
3. Consider using a news API instead of web scraping

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit changes with clear messages
4. Push to the branch and create a Pull Request

## License

MIT License - see LICENSE file for details

## Support

For issues, questions, or suggestions, please open a GitHub issue.
