# Architecture Documentation

## System Overview

The Portfolio Sentiment Intelligence Agent (PSIA) is a multi-agent system that orchestrates several specialized agents to analyze financial news sentiment for user portfolios.

## Agent Architecture

### Base Agent

All agents inherit from `BaseAgent`, which provides:
- Execution timing
- Error handling
- State management
- Logging with agent context

### Agent Pipeline

1. **Portfolio Agent**
   - Fetches user portfolio from database
   - Validates portfolio weights sum to 1.0
   - Returns normalized portfolio structure

2. **News Agent**
   - Fetches articles from NewsAPI (primary)
   - Falls back to Finnhub if insufficient articles
   - Filters by time window (24 hours)
   - Deduplicates articles
   - Stores articles in database

3. **Sentiment Agent**
   - Loads FinBERT model (ProsusAI/finbert)
   - Performs batch inference on articles
   - Maps predictions to sentiment scores (-1 to 1)
   - Stores sentiment scores in database

4. **Aggregation Node**
   - Aggregates sentiments by ticker
   - Applies recency weighting (6h=1.0, 12h=0.8, 24h=0.6)
   - Applies source credibility weighting
   - Calculates confidence-weighted averages

5. **Summarization Agent**
   - Generates 2-3 sentence summaries using LLM
   - Focuses on cause → impact relationships
   - Includes sentiment trends
   - Caches summaries to avoid duplicate API calls

6. **Risk Agent**
   - Calculates portfolio-level sentiment
   - Assesses risk per ticker and overall portfolio
   - Generates signals: hold/monitor/review
   - Stores daily aggregates in database

7. **Email Agent**
   - Formats HTML email report
   - Includes portfolio table, summaries, risk flags
   - Sends via SendGrid
   - Logs delivery status

## Orchestration (LangGraph)

The orchestrator uses LangGraph to manage the workflow:

- **State Management:** TypedDict for type safety
- **Checkpointing:** State persistence for recovery
- **Error Handling:** Graceful failure at each step
- **Parallel Execution:** News fetching and summarization run in parallel

## Data Flow

```
User Request
    ↓
Portfolio Agent → {ticker: weight}
    ↓
News Agent → {ticker: [articles]}
    ↓
Sentiment Agent → {article: sentiment}
    ↓
Aggregation → {ticker: sentiment_score}
    ↓
Summarization Agent → {ticker: summary}
    ↓
Risk Agent → {risk_level, signal, reason}
    ↓
Email Agent → Email Sent
```

## Database Schema

### Core Tables

- **users:** User accounts
- **portfolio:** User holdings (ticker, weight)
- **articles:** News articles with metadata
- **sentiment_scores:** Per-article sentiment analysis
- **portfolio_sentiment:** Daily aggregates per ticker
- **email_log:** Email delivery tracking
- **pipeline_runs:** Execution tracking

## Sentiment Aggregation Formula

### Per-Ticker Aggregation

```
weighted_sentiment = Σ(sentiment_score × confidence × recency_weight × credibility_weight) 
                     / Σ(confidence × recency_weight × credibility_weight)
```

### Portfolio-Level Aggregation

```
portfolio_sentiment = Σ(ticker_sentiment × portfolio_weight)
```

### Risk Score

```
risk_score = abs(weighted_sentiment) × portfolio_weight × (1 - avg_confidence)
```

## Error Handling

- Each agent has try-catch error handling
- Pipeline state tracks errors
- Failed steps are logged to `pipeline_runs` table
- Email delivery failures are logged to `email_log` table

## Performance Optimizations

- **Batch Inference:** Sentiment analysis processes 8-16 articles at once
- **Parallel Execution:** News fetching and summarization run concurrently
- **Connection Pooling:** Database connections are pooled
- **Model Caching:** FinBERT model loaded once and reused
- **Summary Caching:** LLM summaries cached to avoid duplicate calls

## Scalability Considerations

- **Stateless Agents:** Agents can run on different machines
- **Database Indexing:** Key queries are indexed
- **API Rate Limiting:** Respects API rate limits with retries
- **Containerization:** Docker enables easy scaling

## Security

- API keys stored in environment variables
- Database credentials in `.env` (not committed)
- SQL injection prevention via SQLAlchemy ORM
- Email addresses validated before sending

