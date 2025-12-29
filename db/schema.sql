-- Portfolio Sentiment Intelligence Agent Database Schema

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Portfolio table (user holdings)
CREATE TABLE IF NOT EXISTS portfolio (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ticker VARCHAR(10) NOT NULL,
    weight DECIMAL(5, 4) NOT NULL CHECK (weight >= 0 AND weight <= 1),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, ticker)
);

-- Articles table (news articles)
CREATE TABLE IF NOT EXISTS articles (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    headline TEXT NOT NULL,
    content TEXT NOT NULL,
    source VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    published_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    content_hash VARCHAR(64) UNIQUE,  -- For deduplication (headline + source hash)
    INDEX idx_ticker_published (ticker, published_at),
    INDEX idx_published_at (published_at)
);

-- Sentiment scores table (per-article sentiment)
CREATE TABLE IF NOT EXISTS sentiment_scores (
    id SERIAL PRIMARY KEY,
    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    label VARCHAR(20) NOT NULL CHECK (label IN ('positive', 'neutral', 'negative')),
    confidence DECIMAL(5, 4) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    score DECIMAL(5, 4) NOT NULL CHECK (score >= -1 AND score <= 1),
    model_version VARCHAR(50) DEFAULT 'ProsusAI/finbert',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_article_id (article_id)
);

-- Portfolio sentiment table (daily aggregates)
CREATE TABLE IF NOT EXISTS portfolio_sentiment (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    sentiment_score DECIMAL(5, 4) NOT NULL,
    article_count INTEGER NOT NULL DEFAULT 0,
    avg_confidence DECIMAL(5, 4) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, date, ticker),
    INDEX idx_user_date (user_id, date)
);

-- Email log table (delivery tracking)
CREATE TABLE IF NOT EXISTS email_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL CHECK (status IN ('sent', 'failed', 'pending')),
    error_message TEXT,
    INDEX idx_user_sent (user_id, sent_at)
);

-- Pipeline runs table (execution tracking)
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    status VARCHAR(20) NOT NULL CHECK (status IN ('running', 'completed', 'failed')),
    error_message TEXT,
    execution_time_seconds INTEGER,
    INDEX idx_user_started (user_id, started_at),
    INDEX idx_status (status)
);

