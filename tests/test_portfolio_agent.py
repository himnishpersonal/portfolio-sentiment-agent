"""Tests for Portfolio Agent."""

import pytest
from agents.portfolio_agent import PortfolioAgent
from services.portfolio_manager import PortfolioManager


@pytest.fixture
def test_user(db_session):
    """Create test user."""
    user = PortfolioManager.create_user("test@example.com")
    yield user
    # Cleanup handled by db_session fixture


@pytest.fixture
def test_portfolio(test_user):
    """Create test portfolio."""
    portfolio = {"AAPL": 0.5, "MSFT": 0.5}
    PortfolioManager.update_portfolio(test_user.id, portfolio)
    return portfolio


def test_portfolio_agent_execute(test_user, test_portfolio):
    """Test portfolio agent execution."""
    agent = PortfolioAgent()
    result = agent.run({"user_id": test_user.id})

    assert "portfolio" in result
    assert result["portfolio"]["AAPL"] == 0.5
    assert result["portfolio"]["MSFT"] == 0.5


def test_portfolio_agent_user_not_found():
    """Test portfolio agent with non-existent user."""
    agent = PortfolioAgent()
    with pytest.raises(ValueError, match="not found"):
        agent.run({"user_id": 99999}))


