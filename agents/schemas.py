"""Pydantic schemas for agent input/output contracts."""

from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class PortfolioInput(BaseModel):
    """Input schema for Portfolio Agent."""

    user_id: int = Field(..., description="User ID")


class PortfolioOutput(BaseModel):
    """Output schema for Portfolio Agent."""

    portfolio: Dict[str, float] = Field(..., description="Dictionary of ticker to weight")
    user_id: int = Field(..., description="User ID")


class NewsInput(BaseModel):
    """Input schema for News Agent."""

    tickers: List[str] = Field(..., description="List of ticker symbols")


class ArticleData(BaseModel):
    """Article data model."""

    headline: str
    content: str
    source: str
    url: str
    published_at: datetime
    ticker: str


class NewsOutput(BaseModel):
    """Output schema for News Agent."""

    articles_by_ticker: Dict[str, List[ArticleData]] = Field(
        ..., description="Dictionary of ticker to list of articles"
    )


class SentimentInput(BaseModel):
    """Input schema for Sentiment Agent."""

    articles: List[ArticleData] = Field(..., description="List of articles to analyze")


class SentimentResult(BaseModel):
    """Sentiment result for a single article."""

    article_id: int | None = Field(None, description="Article ID from database")
    label: str = Field(..., description="Sentiment label: positive, neutral, or negative")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    score: float = Field(..., ge=-1.0, le=1.0, description="Sentiment score (-1 to 1)")


class SentimentOutput(BaseModel):
    """Output schema for Sentiment Agent."""

    sentiments: List[SentimentResult] = Field(..., description="List of sentiment results")


class SummarizationInput(BaseModel):
    """Input schema for Summarization Agent."""

    ticker: str = Field(..., description="Ticker symbol")
    articles: List[ArticleData] = Field(..., description="List of articles")
    sentiments: List[SentimentResult] = Field(..., description="List of sentiment results")


class SummarizationOutput(BaseModel):
    """Output schema for Summarization Agent."""

    ticker: str = Field(..., description="Ticker symbol")
    summary: str = Field(..., description="Generated summary text")


class RiskInput(BaseModel):
    """Input schema for Risk Agent."""

    portfolio: Dict[str, float] = Field(..., description="Dictionary of ticker to weight")
    ticker_sentiments: Dict[str, float] = Field(
        ..., description="Dictionary of ticker to sentiment score"
    )
    ticker_confidences: Dict[str, float] = Field(
        ..., description="Dictionary of ticker to average confidence"
    )


class RiskOutput(BaseModel):
    """Output schema for Risk Agent."""

    portfolio_sentiment: float = Field(..., description="Overall portfolio sentiment score")
    risk_level: str = Field(..., description="Risk level: low, medium, or high")
    signal: str = Field(..., description="Signal: hold, monitor, or review")
    reason: str = Field(..., description="Reason for risk assessment")
    ticker_risks: Dict[str, str] = Field(..., description="Risk level per ticker")


class EmailInput(BaseModel):
    """Input schema for Email Agent."""

    user_email: str = Field(..., description="User email address")
    portfolio: Dict[str, float] = Field(..., description="Dictionary of ticker to weight")
    ticker_data: Dict[str, Dict[str, Any]] = Field(
        ...,
        description="Dictionary of ticker to data (sentiment, summary, risk_level, articles)",
    )
    portfolio_risk: str = Field(..., description="Overall portfolio risk level")
    date: str = Field(..., description="Report date")


class EmailOutput(BaseModel):
    """Output schema for Email Agent."""

    success: bool = Field(..., description="Whether email was sent successfully")
    error_message: str | None = Field(None, description="Error message if failed")

