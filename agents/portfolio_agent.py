"""Portfolio Agent - fetches and validates user portfolio data."""

from typing import Any, Dict

from db import db_manager, User, Portfolio
from agents.base_agent import BaseAgent
from agents.schemas import PortfolioInput, PortfolioOutput


class PortfolioAgent(BaseAgent):
    """Agent for fetching and validating user portfolio."""

    def __init__(self):
        """Initialize Portfolio Agent."""
        super().__init__("PortfolioAgent")

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch and validate user portfolio.

        Args:
            input_data: Must contain 'user_id'.

        Returns:
            Dictionary with 'portfolio' (ticker: weight) and 'user_id'.
        """
        # Validate input
        portfolio_input = PortfolioInput(**input_data)
        user_id = portfolio_input.user_id

        self.logger.info(f"Fetching portfolio for user {user_id}")

        # Fetch portfolio from database
        with db_manager.get_session() as session:
            # Check if user exists
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")

            # Fetch portfolio items
            portfolio_items = session.query(Portfolio).filter(Portfolio.user_id == user_id).all()

            if not portfolio_items:
                raise ValueError(f"No portfolio found for user {user_id}")

            # Build portfolio dictionary
            portfolio = {item.ticker: float(item.weight) for item in portfolio_items}

            # Validate weights sum to approximately 1.0
            total_weight = sum(portfolio.values())
            tolerance = 0.01  # Allow 1% tolerance

            if abs(total_weight - 1.0) > tolerance:
                self.logger.warning(
                    f"Portfolio weights sum to {total_weight:.4f}, expected 1.0. Normalizing."
                )
                # Normalize weights
                portfolio = {ticker: weight / total_weight for ticker, weight in portfolio.items()}

            self.logger.info(
                f"Portfolio for user {user_id}: {len(portfolio)} tickers, total weight: {sum(portfolio.values()):.4f}"
            )

            # Log portfolio composition
            for ticker, weight in sorted(portfolio.items(), key=lambda x: x[1], reverse=True):
                self.logger.debug(f"  {ticker}: {weight:.2%}")

            # Return output
            output = PortfolioOutput(portfolio=portfolio, user_id=user_id)
            return output.model_dump()

