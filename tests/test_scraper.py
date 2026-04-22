"""Unit tests for the scraper module."""

from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from unittest.mock import MagicMock, patch

import httpx

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

    def test_feed_filters_configured_for_irunfar(self):
        scraper = NewsScraper()
        assert "iRunFar" in scraper.FEED_FILTERS
        assert "Review" in scraper.FEED_FILTERS["iRunFar"]["exclude_title_keywords"]
        assert "Sponsored Post" in scraper.FEED_FILTERS["iRunFar"]["exclude_authors"]
        scraper.client.close()


class TestTimeFromRfc822:
    def test_valid_rfc822_returns_utc_datetime(self):
        scraper = NewsScraper()
        result = scraper._time_from_rfc822("Mon, 01 Jan 2024 10:00:00 +0000")
        assert result is not None
        assert result.tzinfo is not None
        scraper.client.close()

    def test_naive_datetime_gets_utc_assigned(self):
        """Covers the naive dt.replace(tzinfo=utc) branch."""
        scraper = NewsScraper()
        naive_dt = datetime(2024, 1, 1, 10, 0, 0)
        with patch("src.scraper.parsedate_to_datetime", return_value=naive_dt):
            result = scraper._time_from_rfc822("anything")
        assert result is not None
        assert result.tzinfo == timezone.utc
        scraper.client.close()

    def test_invalid_string_returns_none(self):
        """Covers the exception fallback path."""
        scraper = NewsScraper()
        assert scraper._time_from_rfc822("not-a-date") is None
        scraper.client.close()


class TestFetchFromRss:
    def _make_entry(self, title, url, published=None, updated=None, summary="", author=""):
        attrs = {"title": title, "link": url, "summary": summary, "author": author}
        entry = MagicMock()
        entry.get = lambda k, d=None: attrs.get(k, d)
        if published is not None:
            entry.published = published
        else:
            del entry.published
        if updated is not None:
            entry.updated = updated
        else:
            del entry.updated
        return entry

    def _mock_feed(self, scraper, entries, bozo=False):
        mock_resp = MagicMock()
        mock_resp.text = ""
        scraper.client.get = MagicMock(return_value=mock_resp)
        feed = MagicMock()
        feed.bozo = bozo
        feed.bozo_exception = Exception("parse error") if bozo else None
        feed.entries = entries
        return feed

    def _recent(self):
        return format_datetime(datetime.now(timezone.utc) - timedelta(hours=1))

    def test_bozo_feed_logs_warning_and_still_processes(self):
        scraper = NewsScraper()
        entry = self._make_entry("Article", "https://x.com", published=self._recent())
        feed = self._mock_feed(scraper, [entry], bozo=True)
        with patch("src.scraper.feedparser.parse", return_value=feed):
            articles = scraper.fetch_from_rss("http://x.com/feed", "Test")
        assert len(articles) == 1
        scraper.client.close()

    def test_uses_updated_when_published_absent(self):
        scraper = NewsScraper()
        entry = self._make_entry("Article", "https://x.com", updated=self._recent())
        feed = self._mock_feed(scraper, [entry])
        with patch("src.scraper.feedparser.parse", return_value=feed):
            articles = scraper.fetch_from_rss("http://x.com/feed", "Test")
        assert len(articles) == 1
        scraper.client.close()

    def test_excludes_article_matching_title_keyword_filter(self):
        scraper = NewsScraper()
        entry = self._make_entry("Garmin Watch Review", "https://x.com", published=self._recent())
        feed = self._mock_feed(scraper, [entry])
        with patch("src.scraper.feedparser.parse", return_value=feed):
            articles = scraper.fetch_from_rss("http://x.com/feed", "iRunFar")
        assert articles == []
        scraper.client.close()

    def test_excludes_article_matching_author_filter(self):
        scraper = NewsScraper()
        entry = self._make_entry(
            "Race Report", "https://x.com", published=self._recent(), author="Sponsored Post"
        )
        feed = self._mock_feed(scraper, [entry])
        with patch("src.scraper.feedparser.parse", return_value=feed):
            articles = scraper.fetch_from_rss("http://x.com/feed", "iRunFar")
        assert articles == []
        scraper.client.close()

    def test_irunfar_summary_keeps_only_middle_sentence(self):
        title = "The 200-Mile Phenomenon: A Data-Based Look at Their Growth and Demographics"
        raw_summary = (
            f"The post {title} appeared first on iRunFar.\n"
            "A look at demographics and growth data from North America's top 200-plus-mile races.\n"
            f"{title} by Zander Chase."
        )
        scraper = NewsScraper()
        entry = self._make_entry(title, "https://x.com", published=self._recent(), summary=raw_summary)
        feed = self._mock_feed(scraper, [entry])
        with patch("src.scraper.feedparser.parse", return_value=feed):
            articles = scraper.fetch_from_rss("http://x.com/feed", "iRunFar")
        assert articles[0].summary == (
            "A look at demographics and growth data from North America's top 200-plus-mile races."
        )
        scraper.client.close()

    def test_strips_html_from_summary(self):
        scraper = NewsScraper()
        entry = self._make_entry(
            "Article", "https://x.com", published=self._recent(), summary="<p>Bold <b>text</b></p>"
        )
        feed = self._mock_feed(scraper, [entry])
        with patch("src.scraper.feedparser.parse", return_value=feed):
            articles = scraper.fetch_from_rss("http://x.com/feed", "Test")
        assert articles[0].summary == "Bold text"
        scraper.client.close()

    def test_request_error_returns_empty_list(self):
        scraper = NewsScraper()
        scraper.client.get = MagicMock(side_effect=httpx.RequestError("conn failed"))
        assert scraper.fetch_from_rss("http://x.com/feed", "Test") == []
        scraper.client.close()

    def test_unexpected_error_returns_empty_list(self):
        scraper = NewsScraper()
        scraper.client.get = MagicMock(side_effect=ValueError("unexpected"))
        assert scraper.fetch_from_rss("http://x.com/feed", "Test") == []
        scraper.client.close()

