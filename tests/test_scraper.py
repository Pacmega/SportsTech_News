"""Unit tests for the scraper module."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.scraper import NewsArticle, NewsScraper


class TestNewsArticle:
    """Tests for the NewsArticle dataclass."""

    def test_article_creation(self):
        """Test creating a news article."""
        article = NewsArticle(
            title="Test Article",
            url="https://example.com/article",
            summary="Test summary",
            source="Test Source",
            published_at="2026-04-03T10:00:00+00:00",
        )

        assert article.title == "Test Article"
        assert article.url == "https://example.com/article"
        assert article.summary == "Test summary"
        assert article.source == "Test Source"
        assert article.published_at == "2026-04-03T10:00:00+00:00"

    def test_article_minimal(self):
        """Test creating article with minimal fields."""
        article = NewsArticle(title="Title", url="https://example.com")

        assert article.title == "Title"
        assert article.url == "https://example.com"
        assert article.summary is None
        assert article.source is None
        assert article.published_at is None


class TestNewsScraper:
    """Tests for the NewsScraper class."""

    def test_scraper_initialization(self):
        """Test scraper initialization."""
        scraper = NewsScraper(timeout=5.0)
        assert scraper.timeout == 5.0
        assert scraper.HOURS_LOOKBACK == 25
        scraper.client.close()

    def test_scraper_default_timeout(self):
        """Test scraper uses default timeout."""
        scraper = NewsScraper()
        assert scraper.timeout == 10.0
        scraper.client.close()

    def test_scraper_context_manager(self):
        """Test scraper works as context manager."""
        with NewsScraper() as scraper:
            assert scraper.client is not None

    def test_is_recent_with_recent_article(self):
        """Test _is_recent returns True for recent articles."""
        scraper = NewsScraper()

        # Article published 1 hour ago
        published_dt = datetime.now(timezone.utc) - timedelta(hours=1)
        assert scraper._is_recent(published_dt) is True

        scraper.client.close()

    def test_is_recent_with_old_article(self):
        """Test _is_recent returns False for old articles."""
        scraper = NewsScraper()

        # Article published 30 hours ago (beyond 25-hour window)
        published_dt = datetime.now(timezone.utc) - timedelta(hours=30)
        assert scraper._is_recent(published_dt) is False

        scraper.client.close()

    def test_is_recent_with_none(self):
        """Test _is_recent returns False for None datetime."""
        scraper = NewsScraper()
        assert scraper._is_recent(None) is False
        scraper.client.close()

    def test_is_recent_with_naive_datetime(self):
        """Test _is_recent handles naive datetime objects."""
        scraper = NewsScraper()

        # Naive datetime (no timezone info) from 1 hour ago
        published_dt = datetime.now() - timedelta(hours=1)
        assert scraper._is_recent(published_dt) is True

        scraper.client.close()

    def test_rss_feeds_configured(self):
        """Test that RSS feeds are configured."""
        scraper = NewsScraper()
        assert "DC Rainmaker" in scraper.RSS_FEEDS
        assert scraper.RSS_FEEDS["DC Rainmaker"] == "https://www.dcrainmaker.com/feed"
        scraper.client.close()

    def test_get_all_news_returns_list(self):
        """Test get_all_news returns a list."""
        scraper = NewsScraper()
        articles = scraper.get_all_news()
        assert isinstance(articles, list)
        # Don't assert length since it depends on actual feed
        assert all(isinstance(a, NewsArticle) for a in articles)
        scraper.client.close()

