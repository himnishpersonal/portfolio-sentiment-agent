"""Pytest configuration and fixtures."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db import Base, db_manager
from config.settings import settings


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine."""
    # Use in-memory SQLite for testing
    test_db_url = "sqlite:///:memory:"
    engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(test_engine):
    """Create database session for testing."""
    Session = sessionmaker(bind=test_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def mock_newsapi(monkeypatch):
    """Mock NewsAPI service."""
    def mock_fetch_articles(ticker, company_name=None, hours=24):
        from services.news_api import Article
        from datetime import datetime, timedelta
        return [
            Article(
                headline=f"Test article for {ticker}",
                content="This is a test article with sufficient content length for testing purposes." * 10,
                source="Test Source",
                url=f"https://example.com/{ticker}",
                published_at=datetime.utcnow() - timedelta(hours=1),
                ticker=ticker,
            )
        ]
    monkeypatch.setattr("services.news_api.NewsAPIService.fetch_articles", mock_fetch_articles)


@pytest.fixture
def mock_sendgrid(monkeypatch):
    """Mock SendGrid service."""
    def mock_send_report(user_email, report_data):
        return True
    monkeypatch.setattr("services.email_service.EmailService.send_report", mock_send_report)

