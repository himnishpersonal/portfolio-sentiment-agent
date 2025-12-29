"""Portfolio management service."""

import logging
from typing import Dict

from db import db_manager, User, Portfolio

logger = logging.getLogger(__name__)


class PortfolioManager:
    """Service for managing user portfolios."""

    @staticmethod
    def create_user(email: str) -> User:
        """Create a new user.

        Args:
            email: User email address.

        Returns:
            User object.
        """
        with db_manager.get_session() as session:
            # Check if user exists
            existing = session.query(User).filter(User.email == email).first()
            if existing:
                raise ValueError(f"User with email {email} already exists")

            user = User(email=email)
            session.add(user)
            session.commit()
            session.refresh(user)

            logger.info(f"Created user {user.id} with email {email}")
            return user

    @staticmethod
    def add_ticker(user_id: int, ticker: str, weight: float) -> None:
        """Add ticker to user portfolio.

        Args:
            user_id: User ID.
            ticker: Stock ticker symbol.
            weight: Portfolio weight (0.0 to 1.0).
        """
        if not 0 <= weight <= 1:
            raise ValueError(f"Weight must be between 0 and 1, got {weight}")

        with db_manager.get_session() as session:
            # Check if user exists
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")

            # Check if ticker already exists
            existing = (
                session.query(Portfolio)
                .filter(Portfolio.user_id == user_id, Portfolio.ticker == ticker)
                .first()
            )

            if existing:
                existing.weight = weight
            else:
                portfolio_item = Portfolio(user_id=user_id, ticker=ticker, weight=weight)
                session.add(portfolio_item)

            session.commit()
            logger.info(f"Added ticker {ticker} with weight {weight} to user {user_id}")

    @staticmethod
    def update_portfolio(user_id: int, portfolio: Dict[str, float]) -> None:
        """Update entire user portfolio.

        Args:
            user_id: User ID.
            portfolio: Dictionary of ticker to weight.
        """
        if not PortfolioManager.validate_weights(portfolio):
            raise ValueError("Portfolio weights must sum to approximately 1.0")

        with db_manager.get_session() as session:
            # Check if user exists
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")

            # Delete existing portfolio
            session.query(Portfolio).filter(Portfolio.user_id == user_id).delete()

            # Add new portfolio items
            for ticker, weight in portfolio.items():
                portfolio_item = Portfolio(user_id=user_id, ticker=ticker, weight=weight)
                session.add(portfolio_item)

            session.commit()
            logger.info(f"Updated portfolio for user {user_id} with {len(portfolio)} tickers")

    @staticmethod
    def get_user_portfolio(user_id: int) -> Dict[str, float]:
        """Get user portfolio.

        Args:
            user_id: User ID.

        Returns:
            Dictionary of ticker to weight.
        """
        with db_manager.get_session() as session:
            portfolio_items = session.query(Portfolio).filter(Portfolio.user_id == user_id).all()
            return {item.ticker: float(item.weight) for item in portfolio_items}

    @staticmethod
    def remove_ticker(user_id: int, ticker: str) -> None:
        """Remove ticker from user portfolio.

        Args:
            user_id: User ID.
            ticker: Stock ticker symbol to remove.
        """
        with db_manager.get_session() as session:
            # Check if user exists
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")

            # Delete the ticker
            deleted = (
                session.query(Portfolio)
                .filter(Portfolio.user_id == user_id, Portfolio.ticker == ticker)
                .delete()
            )

            if deleted == 0:
                raise ValueError(f"Ticker {ticker} not found in portfolio")

            session.commit()
            logger.info(f"Removed ticker {ticker} from user {user_id} portfolio")

    @staticmethod
    def update_ticker_weight(user_id: int, ticker: str, new_weight: float) -> None:
        """Update the weight of a specific ticker in the portfolio.

        Args:
            user_id: User ID.
            ticker: Stock ticker symbol.
            new_weight: New weight (0.0 to 1.0).

        Raises:
            ValueError: If ticker not found or weight invalid.
        """
        if not 0.0 < new_weight <= 1.0:
            raise ValueError("Weight must be between 0 and 1")

        with db_manager.get_session() as session:
            portfolio_item = (
                session.query(Portfolio)
                .filter(Portfolio.user_id == user_id, Portfolio.ticker == ticker)
                .first()
            )

            if not portfolio_item:
                raise ValueError(f"Ticker {ticker} not found in portfolio")

            portfolio_item.weight = new_weight
            session.commit()
            logger.info(f"Updated {ticker} weight to {new_weight:.2%} for user {user_id}")

    @staticmethod
    def normalize_weights(user_id: int) -> None:
        """Normalize all portfolio weights to sum to 1.0.

        Args:
            user_id: User ID.
        """
        with db_manager.get_session() as session:
            portfolio_items = (
                session.query(Portfolio)
                .filter(Portfolio.user_id == user_id)
                .all()
            )

            if not portfolio_items:
                return

            # Calculate total weight
            total_weight = sum(item.weight for item in portfolio_items)

            if total_weight == 0:
                # Distribute equally if all weights are zero
                equal_weight = 1.0 / len(portfolio_items)
                for item in portfolio_items:
                    item.weight = equal_weight
            else:
                # Normalize to sum to 1.0
                for item in portfolio_items:
                    item.weight = item.weight / total_weight

            session.commit()
            logger.info(f"Normalized portfolio weights for user {user_id}")

    @staticmethod
    def validate_weights(weights: Dict[str, float], tolerance: float = 0.01) -> bool:
        """Validate that portfolio weights sum to 1.0.

        Args:
            weights: Dictionary of ticker to weight.
            tolerance: Allowed deviation from 1.0.

        Returns:
            True if weights are valid, False otherwise.
        """
        total = sum(weights.values())
        return abs(total - 1.0) <= tolerance

