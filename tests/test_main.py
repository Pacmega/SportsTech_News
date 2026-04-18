"""Tests for the main orchestration module."""

from unittest.mock import patch

from src.main import main
from src.scraper import NewsArticle


def _article(url: str = "https://example.com/1", published_at: str = "2026-01-01T10:00:00+00:00"):
    return NewsArticle(title="Test", url=url, source="Test", published_at=published_at)


def _patch_all(rss_articles=None, web_articles=None, send_result=True):
    """Return a tuple of (rss_patch, web_patch, bot_patch) context managers."""
    rss_articles = rss_articles or []
    web_articles = web_articles or []

    rss = patch("src.main.NewsScraper")
    web = patch("src.main.WebScraper")
    bot = patch("src.main.TelegramBot")
    return rss, web, bot, rss_articles, web_articles, send_result


class TestMain:
    def test_returns_0_on_success(self):
        with patch("src.main.NewsScraper") as MockRSS, \
             patch("src.main.WebScraper") as MockWeb, \
             patch("src.main.TelegramBot") as MockBot:
            MockRSS.return_value.__enter__.return_value.get_all_news.return_value = []
            MockWeb.return_value.__enter__.return_value.get_all_news.return_value = []
            MockBot.return_value.__enter__.return_value.send_news_brief.return_value = True

            assert main() == 0

    def test_returns_1_when_send_fails(self):
        with patch("src.main.NewsScraper") as MockRSS, \
             patch("src.main.WebScraper") as MockWeb, \
             patch("src.main.TelegramBot") as MockBot:
            MockRSS.return_value.__enter__.return_value.get_all_news.return_value = []
            MockWeb.return_value.__enter__.return_value.get_all_news.return_value = []
            MockBot.return_value.__enter__.return_value.send_news_brief.return_value = False

            assert main() == 1

    def test_returns_1_on_value_error(self):
        with patch("src.main.NewsScraper") as MockRSS, \
             patch("src.main.WebScraper"), \
             patch("src.main.TelegramBot"):
            MockRSS.return_value.__enter__.side_effect = ValueError("missing token")

            assert main() == 1

    def test_returns_1_on_unexpected_exception(self):
        with patch("src.main.NewsScraper") as MockRSS, \
             patch("src.main.WebScraper"), \
             patch("src.main.TelegramBot"):
            MockRSS.return_value.__enter__.side_effect = RuntimeError("crash")

            assert main() == 1

    def test_deduplicates_same_url_from_rss_and_web(self):
        shared = _article(url="https://dup.com")
        unique = _article(url="https://unique.com")
        captured = []

        with patch("src.main.NewsScraper") as MockRSS, \
             patch("src.main.WebScraper") as MockWeb, \
             patch("src.main.TelegramBot") as MockBot:
            MockRSS.return_value.__enter__.return_value.get_all_news.return_value = [shared]
            MockWeb.return_value.__enter__.return_value.get_all_news.return_value = [shared, unique]
            MockBot.return_value.__enter__.return_value.send_news_brief.side_effect = (
                lambda arts: captured.extend(arts) or True
            )

            main()

        assert len(captured) == 2
        assert sum(1 for a in captured if a.url == "https://dup.com") == 1
        assert any(a.url == "https://unique.com" for a in captured)

    def test_merges_rss_and_web_articles(self):
        rss_article = _article(url="https://rss.com")
        web_article = _article(url="https://web.com")
        captured = []

        with patch("src.main.NewsScraper") as MockRSS, \
             patch("src.main.WebScraper") as MockWeb, \
             patch("src.main.TelegramBot") as MockBot:
            MockRSS.return_value.__enter__.return_value.get_all_news.return_value = [rss_article]
            MockWeb.return_value.__enter__.return_value.get_all_news.return_value = [web_article]
            MockBot.return_value.__enter__.return_value.send_news_brief.side_effect = (
                lambda arts: captured.extend(arts) or True
            )

            main()

        urls = {a.url for a in captured}
        assert "https://rss.com" in urls
        assert "https://web.com" in urls
