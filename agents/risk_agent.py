"""Risk Agent - assesses portfolio risk and generates signals."""

from datetime import date
from typing import Any, Dict

from db import db_manager, PortfolioSentiment
from agents.base_agent import BaseAgent
from agents.schemas import RiskInput, RiskOutput
from services.sentiment_aggregator import aggregate_portfolio_sentiment
from config.settings import settings


class RiskAgent(BaseAgent):
    """Agent for risk assessment."""

    def __init__(self):
        """Initialize Risk Agent."""
        super().__init__("RiskAgent")

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess portfolio risk.

        Args:
            input_data: Must contain:
                - 'portfolio': dict of {ticker: weight}
                - 'ticker_sentiments': dict of {ticker: sentiment_score}
                - 'ticker_confidences': dict of {ticker: avg_confidence}
                - 'ticker_articles': dict of {ticker: list of articles}

        Returns:
            Dictionary with risk assessment results.
        """
        # Validate input
        risk_input = RiskInput(**input_data)
        portfolio = risk_input.portfolio
        ticker_sentiments = risk_input.ticker_sentiments
        ticker_confidences = risk_input.ticker_confidences

        self.logger.info(f"Assessing risk for portfolio with {len(portfolio)} tickers")

        # Calculate portfolio-level sentiment
        portfolio_sentiment = aggregate_portfolio_sentiment(ticker_sentiments, portfolio)

        # Assess risk per ticker
        ticker_risks: Dict[str, str] = {}
        for ticker, weight in portfolio.items():
            sentiment = ticker_sentiments.get(ticker, 0.0)
            confidence = ticker_confidences.get(ticker, 0.5)

            # Calculate risk score - emphasize sentiment magnitude over uncertainty
            # Formula: sentiment magnitude * weight * (1.5 for high confidence, 0.5 for low)
            confidence_multiplier = 0.5 + confidence  # Range: 0.5 to 1.5
            risk_score = abs(sentiment) * weight * confidence_multiplier

            # Map to risk level
            if risk_score < settings.RISK_THRESHOLD_LOW:
                risk_level = "low"
            elif risk_score < settings.RISK_THRESHOLD_HIGH:
                risk_level = "medium"
            else:
                risk_level = "high"

            ticker_risks[ticker] = risk_level

        # Overall portfolio risk - emphasize sentiment magnitude
        avg_risk_score = sum(
            abs(ticker_sentiments.get(ticker, 0.0))
            * weight
            * (0.5 + ticker_confidences.get(ticker, 0.5))  # Confidence multiplier
            for ticker, weight in portfolio.items()
        )

        if avg_risk_score < settings.RISK_THRESHOLD_LOW:
            portfolio_risk = "low"
            signal = "hold"
            reason = "Portfolio sentiment is stable with low risk indicators."
        elif avg_risk_score < settings.RISK_THRESHOLD_HIGH:
            portfolio_risk = "medium"
            signal = "monitor"
            reason = "Portfolio shows moderate sentiment volatility. Monitor closely."
        else:
            portfolio_risk = "high"
            signal = "review"
            reason = "High risk detected. Review portfolio positions and consider adjustments."

        # Store daily aggregates in database
        user_id = input_data.get("user_id")
        if user_id:
            self._store_portfolio_sentiment(
                user_id, portfolio, ticker_sentiments, ticker_confidences, input_data.get("ticker_articles", {})
            )

        # Return output
        output = RiskOutput(
            portfolio_sentiment=portfolio_sentiment,
            risk_level=portfolio_risk,
            signal=signal,
            reason=reason,
            ticker_risks=ticker_risks,
        )
        return output.model_dump()

    def _store_portfolio_sentiment(
        self,
        user_id: int,
        portfolio: Dict[str, float],
        ticker_sentiments: Dict[str, float],
        ticker_confidences: Dict[str, float],
        ticker_articles: Dict[str, list],
    ) -> None:
        """Store daily portfolio sentiment aggregates.

        Args:
            user_id: User ID.
            portfolio: Portfolio weights.
            ticker_sentiments: Ticker sentiment scores.
            ticker_confidences: Ticker confidence scores.
            ticker_articles: Ticker articles (for counting).
        """
        try:
            today = date.today()

            with db_manager.get_session() as session:
                for ticker, sentiment in ticker_sentiments.items():
                    article_count = len(ticker_articles.get(ticker, []))
                    avg_confidence = ticker_confidences.get(ticker, 0.0)

                    # Check if record exists
                    existing = (
                        session.query(PortfolioSentiment)
                        .filter(
                            PortfolioSentiment.user_id == user_id,
                            PortfolioSentiment.date == today,
                            PortfolioSentiment.ticker == ticker,
                        )
                        .first()
                    )

                    if existing:
                        # Update existing
                        existing.sentiment_score = float(sentiment)
                        existing.article_count = article_count
                        existing.avg_confidence = float(avg_confidence)
                    else:
                        # Create new
                        portfolio_sentiment = PortfolioSentiment(
                            user_id=user_id,
                            date=today,
                            ticker=ticker,
                            sentiment_score=float(sentiment),
                            article_count=article_count,
                            avg_confidence=float(avg_confidence),
                        )
                        session.add(portfolio_sentiment)

                session.commit()
                self.logger.info(f"Stored portfolio sentiment for user {user_id}")

        except Exception as e:
            self.logger.error(f"Error storing portfolio sentiment: {e}")

