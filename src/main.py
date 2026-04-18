"""Main entry point for the Sports Tech News Bot."""

import logging
import sys

from dotenv import load_dotenv

from src.scraper import NewsArticle, NewsScraper
from src.telegram_bot import TelegramBot
from src.web_scraper import WebScraper

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> int:
    """
    Main function to orchestrate the news bot workflow.

    Workflow:
    1. Fetch sports tech news from configured sources
    2. Format the news brief
    3. Send via Telegram

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    try:
        logger.info("Starting Sports Tech News Bot...")

        # Step 1: Fetch news
        logger.info("Fetching news from sources...")
        with NewsScraper() as rss_scraper:
            rss_articles = rss_scraper.get_all_news()

        with WebScraper() as web_scraper:
            web_articles = web_scraper.get_all_news()

        seen_urls: set[str] = set()
        articles: list[NewsArticle] = []
        for article in rss_articles + web_articles:
            if article.url not in seen_urls:
                seen_urls.add(article.url)
                articles.append(article)
        articles.sort(key=lambda x: x.published_at or "", reverse=True)

        logger.info(f"Fetched {len(articles)} articles")

        # Step 2: Send via Telegram
        logger.info("Sending news brief via Telegram...")
        with TelegramBot() as bot:
            success = bot.send_news_brief(articles)

        if success:
            logger.info("News brief sent successfully!")
            return 0
        else:
            logger.error("Failed to send news brief")
            return 1

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
