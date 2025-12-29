"""NewsAPI service for fetching financial news articles."""

import hashlib
import logging
from datetime import datetime, timedelta
from typing import List

import requests
from dateutil import parser

from config.settings import settings

logger = logging.getLogger(__name__)


class Article:
    """Article data model."""

    def __init__(
        self,
        headline: str,
        content: str,
        source: str,
        url: str,
        published_at: datetime,
        ticker: str,
    ):
        """Initialize article.

        Args:
            headline: Article headline.
            content: Article content.
            source: News source name.
            url: Article URL.
            published_at: Publication timestamp.
            ticker: Stock ticker symbol.
        """
        self.headline = headline
        self.content = content
        self.source = source
        self.url = url
        self.published_at = published_at
        self.ticker = ticker

    def to_dict(self) -> dict:
        """Convert article to dictionary."""
        return {
            "headline": self.headline,
            "content": self.content,
            "source": self.source,
            "url": self.url,
            "published_at": self.published_at,
            "ticker": self.ticker,
        }

    def content_hash(self) -> str:
        """Generate content hash for deduplication."""
        content_str = f"{self.headline}{self.source}"
        return hashlib.sha256(content_str.encode()).hexdigest()


class NewsAPIService:
    """Service for fetching news from NewsAPI."""

    BASE_URL = "https://newsapi.org/v2"

    def __init__(self, api_key: str | None = None):
        """Initialize NewsAPI service.

        Args:
            api_key: NewsAPI API key. If None, uses settings.NEWSAPI_KEY.
        """
        self.api_key = api_key or settings.NEWSAPI_KEY
        self.session = requests.Session()
        self.session.headers.update({"X-Api-Key": self.api_key})

    def fetch_articles(
        self, ticker: str, company_name: str | None = None, hours: int = 24
    ) -> List[Article]:
        """Fetch articles for a ticker.

        Args:
            ticker: Stock ticker symbol.
            company_name: Company name (optional, for better search).
            hours: Hours to look back for articles.

        Returns:
            List of Article objects.
        """
        try:
            # Calculate time window (timezone-aware)
            from datetime import timezone
            to_date = datetime.now(timezone.utc)
            from_date = to_date - timedelta(hours=hours)

            # Build query
            query_parts = [ticker]
            if company_name:
                query_parts.append(company_name)

            query = f"({' OR '.join(query_parts)}) AND (earnings OR stock OR market OR financial)"

            # Make API request
            params = {
                "q": query,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": 50,  # Get more than needed, then filter
                "from": from_date.isoformat(),
                "to": to_date.isoformat(),
            }

            response = self.session.get(f"{self.BASE_URL}/everything", params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            articles_data = data.get("articles", [])

            # Filter and process articles
            articles = []
            for article_data in articles_data:
                try:
                    # Parse published date
                    published_at = parser.parse(article_data.get("publishedAt", ""))
                    if published_at < from_date:
                        continue

                    # Extract content
                    content = article_data.get("content", "") or article_data.get("description", "")
                    if len(content) < settings.NEWS_MIN_ARTICLE_LENGTH:
                        continue

                    # Truncate content if too long
                    if len(content) > 5000:
                        content = content[:5000]

                    article = Article(
                        headline=article_data.get("title", ""),
                        content=content,
                        source=article_data.get("source", {}).get("name", "Unknown"),
                        url=article_data.get("url", ""),
                        published_at=published_at,
                        ticker=ticker,
                    )

                    articles.append(article)

                    # Limit articles per ticker
                    if len(articles) >= settings.NEWS_MAX_ARTICLES_PER_TICKER:
                        break

                except Exception as e:
                    logger.warning(f"Error processing article: {e}")
                    continue

            logger.info(f"Fetched {len(articles)} articles for {ticker}")
            return articles

        except requests.exceptions.RequestException as e:
            logger.error(f"NewsAPI request failed for {ticker}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching articles for {ticker}: {e}")
            return []

