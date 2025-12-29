"""SQLAlchemy models for database tables."""

from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import Column, Integer, String, Text, DECIMAL, TIMESTAMP, DATE, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """User model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationships
    portfolio_items = relationship("Portfolio", back_populates="user", cascade="all, delete-orphan")
    portfolio_sentiments = relationship(
        "PortfolioSentiment", back_populates="user", cascade="all, delete-orphan"
    )
    email_logs = relationship("EmailLog", back_populates="user", cascade="all, delete-orphan")
    pipeline_runs = relationship("PipelineRun", back_populates="user", cascade="all, delete-orphan")


class Portfolio(Base):
    """Portfolio holdings model."""

    __tablename__ = "portfolio"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    ticker = Column(String(10), nullable=False)
    weight = Column(DECIMAL(5, 4), nullable=False)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="portfolio_items")

    __table_args__ = (Index("idx_user_ticker", "user_id", "ticker", unique=True),)


class Article(Base):
    """News article model."""

    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(10), nullable=False, index=True)
    headline = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String(255), nullable=False)
    url = Column(Text, nullable=False)
    published_at = Column(TIMESTAMP, nullable=False, index=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    content_hash = Column(String(64), unique=True, index=True)

    # Relationships
    sentiment_scores = relationship("SentimentScore", back_populates="article", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_ticker_published", "ticker", "published_at"),
        Index("idx_published_at", "published_at"),
    )


class SentimentScore(Base):
    """Sentiment score model."""

    __tablename__ = "sentiment_scores"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True)
    label = Column(String(20), nullable=False)  # positive, neutral, negative
    confidence = Column(DECIMAL(5, 4), nullable=False)
    score = Column(DECIMAL(5, 4), nullable=False)  # -1.0 to 1.0
    model_version = Column(String(50), default="ProsusAI/finbert")
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationships
    article = relationship("Article", back_populates="sentiment_scores")


class PortfolioSentiment(Base):
    """Daily portfolio sentiment aggregate model."""

    __tablename__ = "portfolio_sentiment"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date = Column(DATE, nullable=False)
    ticker = Column(String(10), nullable=False)
    sentiment_score = Column(DECIMAL(5, 4), nullable=False)
    article_count = Column(Integer, nullable=False, default=0)
    avg_confidence = Column(DECIMAL(5, 4), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="portfolio_sentiments")

    __table_args__ = (
        Index("idx_user_date_ticker", "user_id", "date", "ticker", unique=True),
        Index("idx_user_date", "user_id", "date"),
    )


class EmailLog(Base):
    """Email delivery log model."""

    __tablename__ = "email_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    sent_at = Column(TIMESTAMP, default=datetime.utcnow, index=True)
    status = Column(String(20), nullable=False)  # sent, failed, pending
    error_message = Column(Text)

    # Relationships
    user = relationship("User", back_populates="email_logs")

    __table_args__ = (Index("idx_user_sent", "user_id", "sent_at"),)


class PipelineRun(Base):
    """Pipeline execution tracking model."""

    __tablename__ = "pipeline_runs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    started_at = Column(TIMESTAMP, default=datetime.utcnow, index=True)
    completed_at = Column(TIMESTAMP)
    status = Column(String(20), nullable=False, index=True)  # running, completed, failed
    error_message = Column(Text)
    execution_time_seconds = Column(Integer)

    # Relationships
    user = relationship("User", back_populates="pipeline_runs")

    __table_args__ = (
        Index("idx_user_started", "user_id", "started_at"),
        Index("idx_status", "status"),
    )

