"""Module for sending news briefs via Telegram."""

import os
from typing import Optional

import httpx

from src.scraper import NewsArticle


class TelegramBot:
    """Handles sending news briefs to Telegram."""

    API_URL = "https://api.telegram.org"

    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None) -> None:
        """
        Initialize the Telegram bot.

        Args:
            bot_token: Telegram bot token. If None, reads from TELEGRAM_BOT_TOKEN env variable.
            chat_id: Telegram chat ID. If None, reads from TELEGRAM_CHAT_ID env variable.

        Raises:
            ValueError: If bot token or chat ID are not provided and not in environment.
        """
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")

        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        if not self.chat_id:
            raise ValueError("TELEGRAM_CHAT_ID is required")

        self.client = httpx.Client()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.client.close()

    def send_message(self, text: str) -> bool:
        """
        Send a message to Telegram chat.

        Args:
            text: The message text to send.

        Returns:
            True if message sent successfully, False otherwise.
        """
        url = f"{self.API_URL}/bot{self.bot_token}/sendMessage"

        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
        }

        try:
            response = self.client.post(url, json=payload)
            response.raise_for_status()
            return True
        except httpx.RequestError as e:
            print(f"Error sending Telegram message: {e}")
            return False

    def format_news_brief(self, articles: list[NewsArticle], max_articles: int = 5) -> str:
        """
        Format a list of articles into a Telegram-friendly message.

        Args:
            articles: List of news articles to format.
            max_articles: Maximum number of articles to include.

        Returns:
            Formatted message string in HTML.
        """
        if not articles:
            return (
                "<b>Sports Tech News Brief</b>\n\n"
                "No news articles found for today."
            )

        limited_articles = articles[:max_articles]

        message = "<b>🏆 Sports Tech News Brief</b>\n\n"

        for idx, article in enumerate(limited_articles, 1):
            message += f"<b>{idx}. {article.title}</b>\n"

            if article.source:
                message += f"<i>Source: {article.source}</i>\n"

            if article.summary:
                message += f"{article.summary}\n"

            message += f"<a href=\"{article.url}\">Read more</a>\n\n"

        message += "---\n<i>Daily brief generated automatically.</i>"

        return message

    def send_news_brief(self, articles: list[NewsArticle]) -> bool:
        """
        Fetch news and send a formatted brief to Telegram.

        Args:
            articles: List of articles to include in the brief.

        Returns:
            True if brief sent successfully, False otherwise.
        """
        brief_message = self.format_news_brief(articles)
        return self.send_message(brief_message)
