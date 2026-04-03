"""Tests for telegram_bot module."""

from unittest.mock import MagicMock, patch

import pytest

from src.scraper import NewsArticle
from src.telegram_bot import TelegramBot


class TestTelegramBot:
    """Tests for the TelegramBot class."""

    def test_bot_initialization_with_params(self):
        """Test bot initialization with explicit parameters."""
        bot = TelegramBot(bot_token="test_token", chat_id="test_chat")
        assert bot.bot_token == "test_token"
        assert bot.chat_id == "test_chat"
        bot.client.close()

    def test_bot_initialization_missing_token(self):
        """Test bot raises error when token is missing."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN"):
                TelegramBot(chat_id="test_chat")

    def test_bot_initialization_missing_chat_id(self):
        """Test bot raises error when chat_id is missing."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="TELEGRAM_CHAT_ID"):
                TelegramBot(bot_token="test_token")

    def test_format_news_brief_empty(self):
        """Test formatting empty news brief."""
        bot = TelegramBot(bot_token="test", chat_id="test")
        message = bot.format_news_brief([])

        assert "No news articles found" in message
        bot.client.close()

    def test_format_news_brief_with_articles(self):
        """Test formatting news brief with articles."""
        bot = TelegramBot(bot_token="test", chat_id="test")

        articles = [
            NewsArticle(
                title="Article 1",
                url="https://example.com/1",
                summary="Summary 1",
                source="Source 1",
            ),
            NewsArticle(
                title="Article 2",
                url="https://example.com/2",
                summary="Summary 2",
                source="Source 2",
            ),
        ]

        message = bot.format_news_brief(articles)

        assert "Article 1" in message
        assert "Article 2" in message
        assert "Summary 1" in message
        assert "Summary 2" in message
        assert "Source 1" in message
        assert "Source 2" in message
        bot.client.close()

    def test_format_news_brief_max_articles(self):
        """Test formatting respects max_articles limit."""
        bot = TelegramBot(bot_token="test", chat_id="test")

        articles = [
            NewsArticle(title=f"Article {i}", url=f"https://example.com/{i}")
            for i in range(10)
        ]

        message = bot.format_news_brief(articles, max_articles=3)

        assert message.count("<b>") <= 7  # 3 articles + header
        bot.client.close()

    def test_bot_context_manager(self):
        """Test bot works as context manager."""
        with TelegramBot(bot_token="test", chat_id="test") as bot:
            assert bot.client is not None
