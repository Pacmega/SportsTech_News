"""Unit tests for the scraper module."""

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
        )

        assert article.title == "Test Article"
        assert article.url == "https://example.com/article"
        assert article.summary == "Test summary"
        assert article.source == "Test Source"

    def test_article_minimal(self):
        """Test creating article with minimal fields."""
        article = NewsArticle(title="Title", url="https://example.com")

        assert article.title == "Title"
        assert article.url == "https://example.com"
        assert article.summary is None
        assert article.source is None


class TestNewsScraper:
    """Tests for the NewsScraper class."""

    def test_scraper_initialization(self):
        """Test scraper initialization."""
        scraper = NewsScraper(timeout=5.0)
        assert scraper.timeout == 5.0
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

    def test_fetch_news_from_api_returns_articles(self):
        """Test fetch_news_from_api returns articles."""
        with NewsScraper() as scraper:
            articles = scraper._sync_fetch_news_from_api()

        assert len(articles) > 0
        assert all(isinstance(a, NewsArticle) for a in articles)

    def test_get_all_news(self):
        """Test get_all_news aggregates articles."""
        with NewsScraper() as scraper:
            articles = scraper.get_all_news()

        assert len(articles) > 0
        assert all(isinstance(a, NewsArticle) for a in articles)
