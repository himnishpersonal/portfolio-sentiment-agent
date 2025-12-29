"""Tests for Portfolio Manager."""

import pytest
from services.portfolio_manager import PortfolioManager


def test_create_user(db_session):
    """Test user creation."""
    user = PortfolioManager.create_user("test2@example.com")
    assert user.id is not None
    assert user.email == "test2@example.com"


def test_create_duplicate_user(db_session):
    """Test creating duplicate user."""
    PortfolioManager.create_user("duplicate@example.com")
    with pytest.raises(ValueError, match="already exists"):
        PortfolioManager.create_user("duplicate@example.com")


def test_add_ticker(db_session):
    """Test adding ticker to portfolio."""
    user = PortfolioManager.create_user("test3@example.com")
    PortfolioManager.add_ticker(user.id, "AAPL", 0.5)
    portfolio = PortfolioManager.get_user_portfolio(user.id)
    assert portfolio["AAPL"] == 0.5


def test_validate_weights():
    """Test weight validation."""
    assert PortfolioManager.validate_weights({"AAPL": 0.5, "MSFT": 0.5})
    assert not PortfolioManager.validate_weights({"AAPL": 0.5, "MSFT": 0.6})
    assert PortfolioManager.validate_weights({"AAPL": 0.99, "MSFT": 0.01}, tolerance=0.02)

