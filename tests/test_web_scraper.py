"""Tests for the web_scraper module."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import httpx

from src.scraper import NewsArticle
from src.web_scraper import BaseSiteScraper, WebScraper


class _StubScraper(BaseSiteScraper):
    """Minimal concrete BaseSiteScraper for testing."""

    SOURCE_NAME = "Stub"

    def fetch(self) -> list[NewsArticle]:
        return []


def _make_stub(hours_lookback: int = 25) -> _StubScraper:
    return _StubScraper(client=MagicMock(spec=httpx.Client), hours_lookback=hours_lookback)


class TestBaseSiteScraperIsRecent:
    def test_recent_article(self):
        scraper = _make_stub()
        assert scraper._is_recent(datetime.now(timezone.utc) - timedelta(hours=1)) is True

    def test_old_article(self):
        scraper = _make_stub()
        assert scraper._is_recent(datetime.now(timezone.utc) - timedelta(hours=30)) is False

    def test_none_returns_false(self):
        assert _make_stub()._is_recent(None) is False

    def test_naive_datetime_treated_as_utc(self):
        scraper = _make_stub()
        dt = datetime.now() - timedelta(hours=1)  # naive
        assert scraper._is_recent(dt) is True


class TestWebScraper:
    def test_init_defaults(self):
        with WebScraper() as scraper:
            assert scraper.HOURS_LOOKBACK == 25
            assert scraper._scrapers == []

    def test_context_manager_closes_client(self):
        scraper = WebScraper()
        scraper.__enter__()
        scraper.__exit__(None, None, None)
        assert scraper.client.is_closed

    def test_get_all_news_empty_registry(self):
        with WebScraper() as scraper:
            assert scraper.get_all_news() == []

    def test_get_all_news_returns_articles_from_site_scraper(self):
        article = NewsArticle(
            title="Trail Race", url="https://a.com", source="Stub",
            published_at="2026-01-01T10:00:00+00:00",
        )
        mock_site = MagicMock(spec=BaseSiteScraper)
        mock_site.fetch.return_value = [article]

        with WebScraper() as web_scraper:
            web_scraper._scrapers = [mock_site]
            result = web_scraper.get_all_news()

        assert result == [article]

    def test_get_all_news_site_scraper_exception_is_caught(self):
        mock_site = MagicMock(spec=BaseSiteScraper)
        mock_site.fetch.side_effect = RuntimeError("boom")

        with WebScraper() as web_scraper:
            web_scraper._scrapers = [mock_site]
            result = web_scraper.get_all_news()

        assert result == []

    def test_get_all_news_sorts_newest_first(self):
        older = NewsArticle(
            title="Old", url="https://a.com", published_at="2026-01-01T08:00:00+00:00"
        )
        newer = NewsArticle(
            title="New", url="https://b.com", published_at="2026-01-01T10:00:00+00:00"
        )
        mock_site = MagicMock(spec=BaseSiteScraper)
        mock_site.fetch.return_value = [older, newer]

        with WebScraper() as web_scraper:
            web_scraper._scrapers = [mock_site]
            result = web_scraper.get_all_news()

        assert result[0] == newer
        assert result[1] == older
