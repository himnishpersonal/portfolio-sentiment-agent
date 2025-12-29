"""Tests for News Agent."""

import pytest
from agents.news_agent import NewsAgent
from agents.schemas import NewsInput


def test_news_agent_execute(mock_newsapi):
    """Test news agent execution."""
    agent = NewsAgent()
    result = agent.run({"tickers": ["AAPL", "MSFT"]})

    assert "articles_by_ticker" in result
    assert "AAPL" in result["articles_by_ticker"]
    assert "MSFT" in result["articles_by_ticker"]


def test_news_agent_empty_tickers():
    """Test news agent with empty ticker list."""
    agent = NewsAgent()
    result = agent.run({"tickers": []})

    assert "articles_by_ticker" in result
    assert result["articles_by_ticker"] == {}

