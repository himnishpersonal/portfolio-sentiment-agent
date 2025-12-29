"""Summarization Agent - generates concise summaries using LLM."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict

from agents.base_agent import BaseAgent
from agents.schemas import (
    SummarizationInput,
    SummarizationOutput,
    ArticleData,
    SentimentResult,
)
from services.llm_service import get_llm_service, Sentiment
from services.news_api import Article


class SummarizationAgent(BaseAgent):
    """Agent for generating article summaries."""

    def __init__(self):
        """Initialize Summarization Agent."""
        super().__init__("SummarizationAgent")
        self.llm_service = get_llm_service()

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summaries for all tickers.

        Args:
            input_data: Must contain 'ticker_data' with structure:
                {ticker: {articles: List[ArticleData], sentiments: List[SentimentResult]}}

        Returns:
            Dictionary with 'summaries_by_ticker'.
        """
        ticker_data = input_data.get("ticker_data", {})

        if not ticker_data:
            self.logger.warning("No ticker data provided for summarization")
            return {"summaries_by_ticker": {}}

        self.logger.info(f"Generating summaries for {len(ticker_data)} tickers")

        # Generate summaries in parallel
        summaries_by_ticker: Dict[str, str] = {}
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_ticker = {
                executor.submit(
                    self._generate_summary_for_ticker,
                    ticker,
                    data.get("articles", []),
                    data.get("sentiments", []),
                ): ticker
                for ticker, data in ticker_data.items()
            }

            for future in as_completed(future_to_ticker):
                ticker = future_to_ticker[future]
                try:
                    summary = future.result()
                    summaries_by_ticker[ticker] = summary
                except Exception as e:
                    self.logger.error(f"Error generating summary for {ticker}: {e}")
                    summaries_by_ticker[ticker] = f"{ticker}: Unable to generate summary."

        self.logger.info(f"Generated {len(summaries_by_ticker)} summaries")

        return {"summaries_by_ticker": summaries_by_ticker}

    def _generate_summary_for_ticker(
        self, ticker: str, articles: list[ArticleData], sentiments: list[SentimentResult]
    ) -> str:
        """Generate summary for a single ticker.

        Args:
            ticker: Stock ticker symbol.
            articles: List of articles.
            sentiments: List of sentiment results.

        Returns:
            Summary text.
        """
        if not articles:
            self.logger.warning(f"No articles provided for {ticker}")
            return f"{ticker}: No articles available for summary."
        
        self.logger.info(f"Generating summary for {ticker} with {len(articles)} articles")
        # Log first article headline for debugging
        if articles:
            first_article = articles[0]
            headline = first_article.get("headline", "") if isinstance(first_article, dict) else first_article.headline
            content = first_article.get("content", "") if isinstance(first_article, dict) else first_article.content
            self.logger.debug(f"First article for {ticker}: {headline[:100]}")
            
            # Check if any article mentions the ticker (case-insensitive)
            ticker_mentioned = False
            for article in articles:
                article_headline = article.get("headline", "") if isinstance(article, dict) else article.headline
                article_content = article.get("content", "") if isinstance(article, dict) else article.content
                combined_text = (article_headline + " " + article_content).upper()
                if ticker.upper() in combined_text:
                    ticker_mentioned = True
                    break
            
            if not ticker_mentioned:
                self.logger.warning(f"Ticker {ticker} not found in any article headlines/content. Articles may be generic.")
        
        # Convert ArticleData/dict to Article objects
        article_objects = []
        for article in articles:
            # Handle both ArticleData objects and dicts
            if isinstance(article, dict):
                article_objects.append(Article(
                    headline=article.get("headline", ""),
                    content=article.get("content", ""),
                    source=article.get("source", ""),
                    url=article.get("url", ""),
                    published_at=article.get("published_at"),
                    ticker=article.get("ticker", ticker),
                ))
            else:
                article_objects.append(Article(
                    headline=article.headline,
                    content=article.content,
                    source=article.source,
                    url=article.url,
                    published_at=article.published_at,
                    ticker=article.ticker,
                ))

        # Convert SentimentResult/dict to Sentiment objects
        sentiment_objects = []
        for sentiment in sentiments:
            # Handle both SentimentResult objects and dicts
            if isinstance(sentiment, dict):
                sentiment_objects.append(Sentiment(
                    label=sentiment.get("label", "neutral"),
                    confidence=sentiment.get("confidence", 0.5),
                    score=sentiment.get("score", 0.0),
                ))
            else:
                sentiment_objects.append(Sentiment(
                    label=sentiment.label,
                    confidence=sentiment.confidence,
                    score=sentiment.score,
                ))

        # Generate summary using LLM service
        summary = self.llm_service.summarize(ticker, article_objects, sentiment_objects)

        return summary

