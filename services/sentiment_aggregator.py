"""Sentiment aggregation logic with recency and credibility weighting."""

import logging
from datetime import datetime, timedelta
from typing import List

from config.settings import settings
from services.news_api import Article
from services.llm_service import Sentiment

logger = logging.getLogger(__name__)


def get_source_credibility_weight(source: str) -> float:
    """Get credibility weight for a news source.

    Args:
        source: News source name.

    Returns:
        Credibility weight (0.0 to 1.0).
    """
    source_lower = source.lower()

    if "reuters" in source_lower:
        return settings.SOURCE_WEIGHT_REUTERS
    elif "bloomberg" in source_lower:
        return settings.SOURCE_WEIGHT_BLOOMBERG
    elif "cnbc" in source_lower:
        return settings.SOURCE_WEIGHT_CNBC
    else:
        return settings.SOURCE_WEIGHT_DEFAULT


def get_recency_weight(published_at: datetime, now: datetime | None = None) -> float:
    """Get recency weight for an article.

    Args:
        published_at: Article publication timestamp.
        now: Current timestamp. If None, uses current time.

    Returns:
        Recency weight (0.0 to 1.0).
    """
    if now is None:
        from datetime import timezone
        now = datetime.now(timezone.utc)

    age_hours = (now - published_at).total_seconds() / 3600

    if age_hours <= 6:
        return settings.RECENCY_WEIGHT_6H
    elif age_hours <= 12:
        return settings.RECENCY_WEIGHT_12H
    elif age_hours <= 24:
        return settings.RECENCY_WEIGHT_24H
    else:
        return 0.0  # Articles older than 24 hours get zero weight


def aggregate_ticker_sentiment(
    articles: List[Article], sentiments: List[Sentiment]
) -> tuple[float, float]:
    """Aggregate sentiment scores for a ticker.

    Args:
        articles: List of articles.
        sentiments: List of sentiment scores (must match articles order).

    Returns:
        Tuple of (weighted_sentiment_score, average_confidence).
    """
    if not articles or not sentiments:
        return 0.0, 0.0

    if len(articles) != len(sentiments):
        logger.warning("Mismatch between articles and sentiments count")
        return 0.0, 0.0

    from datetime import timezone
    now = datetime.now(timezone.utc)
    weighted_sum = 0.0
    weight_sum = 0.0
    confidence_sum = 0.0

    for article, sentiment in zip(articles, sentiments):
        # Calculate weights
        recency_weight = get_recency_weight(article.published_at, now)
        credibility_weight = get_source_credibility_weight(article.source)
        confidence = sentiment.confidence

        # Combined weight
        combined_weight = recency_weight * credibility_weight * confidence

        # Add to weighted sum
        weighted_sum += sentiment.score * combined_weight
        weight_sum += combined_weight
        confidence_sum += confidence

    # Calculate weighted average
    if weight_sum > 0:
        weighted_sentiment = weighted_sum / weight_sum
    else:
        weighted_sentiment = 0.0

    # Calculate average confidence
    avg_confidence = confidence_sum / len(sentiments) if sentiments else 0.0

    return weighted_sentiment, avg_confidence


def aggregate_portfolio_sentiment(
    ticker_sentiments: dict[str, float], portfolio_weights: dict[str, float]
) -> float:
    """Aggregate sentiment scores across portfolio.

    Args:
        ticker_sentiments: Dictionary of ticker to sentiment score.
        portfolio_weights: Dictionary of ticker to portfolio weight.

    Returns:
        Portfolio-level sentiment score.
    """
    portfolio_sentiment = 0.0

    for ticker, sentiment in ticker_sentiments.items():
        weight = portfolio_weights.get(ticker, 0.0)
        portfolio_sentiment += sentiment * weight

    return portfolio_sentiment

