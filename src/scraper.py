"""Module for scraping and fetching sports technology news via RSS feeds."""

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Optional

import feedparser
import httpx

logger = logging.getLogger(__name__)


@dataclass
class NewsArticle:
    """Represents a single news article."""

    title: str
    url: str
    summary: Optional[str] = None
    source: Optional[str] = None
    published_at: Optional[str] = None


class NewsScraper:
    """Handles fetching sports technology news from RSS feeds."""

    # Dictionary of RSS feeds to monitor
    RSS_FEEDS = {
        "DC Rainmaker": "https://www.dcrainmaker.com/feed",
        # Add more feeds as needed:
        # "Another Source": "https://example.com/feed",
    }

    # Filter articles published within the last N hours
    HOURS_LOOKBACK = 25

    def __init__(self, timeout: float = 10.0) -> None:
        """
        Initialize the news scraper.

        Args:
            timeout: HTTP request timeout in seconds.
        """
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.client.close()

    def _time_from_rfc822(self, rfc822_str: str) -> Optional[datetime]:
        """
        Parse RFC 2822 formatted date string to datetime.

        Args:
            rfc822_str: RFC 2822 formatted date string from RSS feed.

        Returns:
            datetime object in UTC, or None if parsing fails.
        """
        try:
            dt = parsedate_to_datetime(rfc822_str)
            # Convert to UTC if it has timezone info
            if dt.tzinfo is not None:
                return dt.astimezone(timezone.utc)
            # If naive, assume UTC
            return dt.replace(tzinfo=timezone.utc)
        except (TypeError, ValueError, AttributeError):
            return None

    def _is_recent(self, published_datetime: Optional[datetime]) -> bool:
        """
        Check if an article was published within the lookback window.

        Args:
            published_datetime: The publish datetime of the article.

        Returns:
            True if article is within HOURS_LOOKBACK hours ago, False otherwise.
        """
        if published_datetime is None:
            return False

        # Ensure published_datetime is timezone-aware (UTC)
        if published_datetime.tzinfo is None:
            published_datetime = published_datetime.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        lookback_threshold = now - timedelta(hours=self.HOURS_LOOKBACK)

        return published_datetime >= lookback_threshold

    def fetch_from_rss(self, feed_url: str, source_name: str) -> list[NewsArticle]:
        """
        Fetch articles from an RSS feed.

        Args:
            feed_url: The URL of the RSS feed.
            source_name: Display name for the source.

        Returns:
            List of NewsArticle objects from the feed, filtered by recency.
        """
        articles = []

        try:
            response = self.client.get(feed_url)
            response.raise_for_status()

            feed = feedparser.parse(response.text)

            if feed.bozo:
                logger.warning(
                    f"Feed parsing warnings for {source_name}: {feed.bozo_exception}"
                )

            for entry in feed.entries:
                # Extract published date
                published_dt = None
                if hasattr(entry, "published"):
                    published_dt = self._time_from_rfc822(entry.published)
                elif hasattr(entry, "updated"):
                    published_dt = self._time_from_rfc822(entry.updated)

                # Filter by recency
                if not self._is_recent(published_dt):
                    continue

                # Extract article details
                title = entry.get("title", "No title")
                url = entry.get("link", "")
                summary = entry.get("summary", "")

                # Clean up HTML from summary if present
                if summary:
                    # Simple cleanup: remove common HTML tags
                    summary = re.sub(r"<[^>]+>", "", summary)
                    summary = summary.strip()

                published_at = published_dt.isoformat() if published_dt else None

                article = NewsArticle(
                    title=title,
                    url=url,
                    summary=summary if summary else None,
                    source=source_name,
                    published_at=published_at,
                )
                articles.append(article)

            logger.info(
                f"Fetched {len(articles)} recent articles from {source_name}"
            )

        except httpx.RequestError as e:
            logger.error(f"Error fetching RSS feed from {source_name}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error parsing feed from {source_name}: {e}")

        return articles

    def get_all_news(self) -> list[NewsArticle]:
        """
        Fetch news from all configured RSS feed sources.

        Articles are filtered to only include those published in the last
        HOURS_LOOKBACK hours, and are sorted by publication date (newest first).

        Returns:
            Combined and sorted list of all fetched articles.
        """
        all_articles = []

        for source_name, feed_url in self.RSS_FEEDS.items():
            articles = self.fetch_from_rss(feed_url, source_name)
            all_articles.extend(articles)

        # Sort by publication date (newest first)
        all_articles.sort(
            key=lambda x: x.published_at or "",
            reverse=True,
        )

        logger.info(f"Total recent articles retrieved: {len(all_articles)}")

        return all_articles
