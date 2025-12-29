"""News Agent - fetches, filters, and deduplicates news articles."""

import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List

from db import db_manager, Article as ArticleModel
from agents.base_agent import BaseAgent
from agents.schemas import NewsInput, NewsOutput, ArticleData
from services.news_api import NewsAPIService, Article
from services.finnhub_api import FinnhubService
from config.settings import settings


class NewsAgent(BaseAgent):
    """Agent for fetching news articles."""

    def __init__(self):
        """Initialize News Agent."""
        super().__init__("NewsAgent")
        self.newsapi_service = NewsAPIService()
        self.finnhub_service = FinnhubService()

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch articles for all tickers.

        Args:
            input_data: Must contain 'tickers' list.

        Returns:
            Dictionary with 'articles_by_ticker'.
        """
        # Validate input
        news_input = NewsInput(**input_data)
        tickers = news_input.tickers

        self.logger.info(f"Fetching news for {len(tickers)} tickers")

        # Fetch articles in parallel
        articles_by_ticker: Dict[str, List[Article]] = {}
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_ticker = {
                executor.submit(self._fetch_articles_for_ticker, ticker): ticker
                for ticker in tickers
            }

            for future in as_completed(future_to_ticker):
                ticker = future_to_ticker[future]
                try:
                    articles = future.result()
                    articles_by_ticker[ticker] = articles
                except Exception as e:
                    self.logger.error(f"Error fetching articles for {ticker}: {e}")
                    articles_by_ticker[ticker] = []

        # Store articles in database and convert to ArticleData
        articles_by_ticker_data: Dict[str, List[ArticleData]] = {}
        with db_manager.get_session() as session:
            for ticker, articles in articles_by_ticker.items():
                article_data_list = []
                seen_hashes = set()

                for article in articles:
                    # Check for duplicates
                    content_hash = article.content_hash()
                    if content_hash in seen_hashes:
                        continue

                    # Check if article already exists in database
                    existing = (
                        session.query(ArticleModel)
                        .filter(ArticleModel.content_hash == content_hash)
                        .first()
                    )

                    if existing:
                        # Use existing article
                        article_data_list.append(
                            ArticleData(
                                headline=existing.headline,
                                content=existing.content,
                                source=existing.source,
                                url=existing.url,
                                published_at=existing.published_at,
                                ticker=existing.ticker,
                            )
                        )
                    else:
                        # Create new article
                        db_article = ArticleModel(
                            ticker=article.ticker,
                            headline=article.headline,
                            content=article.content,
                            source=article.source,
                            url=article.url,
                            published_at=article.published_at,
                            content_hash=content_hash,
                        )
                        session.add(db_article)
                        session.flush()  # Get the ID

                        article_data_list.append(
                            ArticleData(
                                headline=db_article.headline,
                                content=db_article.content,
                                source=db_article.source,
                                url=db_article.url,
                                published_at=db_article.published_at,
                                ticker=db_article.ticker,
                            )
                        )

                    seen_hashes.add(content_hash)

                articles_by_ticker_data[ticker] = article_data_list
                self.logger.info(f"Stored {len(article_data_list)} articles for {ticker}")

        # Return output
        output = NewsOutput(articles_by_ticker=articles_by_ticker_data)
        return output.model_dump()

    def _fetch_articles_for_ticker(self, ticker: str) -> List[Article]:
        """Fetch articles for a single ticker with fallback logic.

        Args:
            ticker: Stock ticker symbol.

        Returns:
            List of Article objects.
        """
        # Try NewsAPI first
        articles = self.newsapi_service.fetch_articles(
            ticker=ticker, hours=settings.NEWS_TIME_WINDOW_HOURS
        )

        # Fallback to Finnhub if insufficient articles
        if len(articles) < 3:
            self.logger.info(f"Only {len(articles)} articles from NewsAPI for {ticker}, trying Finnhub")
            finnhub_articles = self.finnhub_service.fetch_articles(
                ticker=ticker, hours=settings.NEWS_TIME_WINDOW_HOURS
            )

            # Merge articles, avoiding duplicates
            existing_urls = {article.url for article in articles}
            for article in finnhub_articles:
                if article.url not in existing_urls:
                    articles.append(article)

            self.logger.info(f"Total articles for {ticker} after fallback: {len(articles)}")

        return articles

