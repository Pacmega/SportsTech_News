"""Module for scraping sports technology news from sites without RSS feeds."""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from bs4 import BeautifulSoup  # noqa: F401 — available for site scraper subclasses

from src.scraper import NewsArticle

logger = logging.getLogger(__name__)


class BaseSiteScraper(ABC):
    """Abstract base class for per-site HTML scrapers."""

    SOURCE_NAME: str = ""

    def __init__(self, client: httpx.Client, hours_lookback: int) -> None:
        self.client = client
        self.hours_lookback = hours_lookback

    @abstractmethod
    def fetch(self) -> list[NewsArticle]:
        """Fetch and return recent articles from the site."""
        ...

    def _is_recent(self, published_datetime: Optional[datetime]) -> bool:
        if published_datetime is None:
            return False
        if published_datetime.tzinfo is None:
            published_datetime = published_datetime.replace(tzinfo=timezone.utc)
        threshold = datetime.now(timezone.utc) - timedelta(hours=self.hours_lookback)
        return published_datetime >= threshold


class WebScraper:
    """Orchestrates all registered HTML site scrapers."""

    HOURS_LOOKBACK = 25

    def __init__(self, timeout: float = 10.0) -> None:
        self.client = httpx.Client(
            timeout=timeout,
            headers={"User-Agent": "SportsTechNewsBot/1.0"},
        )
        self._scrapers: list[BaseSiteScraper] = self._build_scrapers()

    def _build_scrapers(self) -> list[BaseSiteScraper]:
        # Register active site scrapers here as they are implemented
        return []

    def get_all_news(self) -> list[NewsArticle]:
        all_articles: list[NewsArticle] = []
        for scraper in self._scrapers:
            try:
                all_articles.extend(scraper.fetch())
            except Exception as e:
                logger.error(f"Error in {scraper.__class__.__name__}: {e}")
        all_articles.sort(key=lambda x: x.published_at or "", reverse=True)
        logger.info(f"Total recent web articles retrieved: {len(all_articles)}")
        return all_articles

    def __enter__(self) -> "WebScraper":
        return self

    def __exit__(self, *args: object) -> None:
        self.client.close()
