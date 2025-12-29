"""Finnhub service for fetching financial news articles (fallback)."""

import hashlib
import logging
from datetime import datetime, timedelta
from typing import List

import requests
from dateutil import parser

from config.settings import settings
from services.news_api import Article

logger = logging.getLogger(__name__)


class FinnhubService:
    """Service for fetching news from Finnhub (fallback to NewsAPI)."""

    BASE_URL = "https://finnhub.io/api/v1"

    def __init__(self, api_key: str | None = None):
        """Initialize Finnhub service.

        Args:
            api_key: Finnhub API key. If None, uses settings.FINNHUB_KEY.
        """
        self.api_key = api_key or settings.FINNHUB_KEY
        self.session = requests.Session()

    def fetch_articles(self, ticker: str, hours: int = 24) -> List[Article]:
        """Fetch articles for a ticker.

        Args:
            ticker: Stock ticker symbol.
            hours: Hours to look back for articles.

        Returns:
            List of Article objects (normalized format).
        """
        try:
            # Calculate time window (Finnhub uses YYYY-MM-DD date format)
            from datetime import timezone
            now = datetime.now(timezone.utc)
            to_date = now.strftime("%Y-%m-%d")
            from_date = (now - timedelta(hours=hours)).strftime("%Y-%m-%d")

            # Make API request
            params = {
                "symbol": ticker,
                "token": self.api_key,
                "from": from_date,
                "to": to_date,
            }

            response = self.session.get(f"{self.BASE_URL}/company-news", params=params, timeout=30)
            response.raise_for_status()

            articles_data = response.json()

            if not isinstance(articles_data, list):
                logger.warning(f"Unexpected response format from Finnhub for {ticker}")
                return []

            # Filter and process articles
            articles = []
            for article_data in articles_data:
                try:
                    # Parse published date (timezone-aware)
                    published_at = datetime.fromtimestamp(
                        article_data.get("datetime", 0), tz=timezone.utc
                    )

                    # Extract content
                    headline = article_data.get("headline", "")
                    summary = article_data.get("summary", "")
                    content = summary if summary else headline

                    if len(content) < settings.NEWS_MIN_ARTICLE_LENGTH:
                        continue

                    # Truncate content if too long
                    if len(content) > 5000:
                        content = content[:5000]

                    article = Article(
                        headline=headline,
                        content=content,
                        source=article_data.get("source", "Unknown"),
                        url=article_data.get("url", ""),
                        published_at=published_at,
                        ticker=ticker,
                    )

                    articles.append(article)

                    # Limit articles per ticker
                    if len(articles) >= settings.NEWS_MAX_ARTICLES_PER_TICKER:
                        break

                except Exception as e:
                    logger.warning(f"Error processing Finnhub article: {e}")
                    continue

            logger.info(f"Fetched {len(articles)} articles from Finnhub for {ticker}")
            return articles

        except requests.exceptions.RequestException as e:
            logger.error(f"Finnhub request failed for {ticker}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching articles from Finnhub for {ticker}: {e}")
            return []

