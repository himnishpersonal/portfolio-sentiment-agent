# Portfolio Sentiment Intelligence Agent (PSIA)
## Comprehensive Technical Documentation

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture Deep Dive](#2-architecture-deep-dive)
3. [Multi-Agent System](#3-multi-agent-system)
4. [Data Flow & Pipeline](#4-data-flow--pipeline)
5. [Database Schema](#5-database-schema)
6. [Frontend (Streamlit)](#6-frontend-streamlit)
7. [External Services & APIs](#7-external-services--apis)
8. [ML Components](#8-ml-components)
9. [Sentiment Aggregation Algorithm](#9-sentiment-aggregation-algorithm)
10. [Risk Assessment Logic](#10-risk-assessment-logic)
11. [Configuration Management](#11-configuration-management)
12. [Deployment Options](#12-deployment-options)
13. [File Structure Reference](#13-file-structure-reference)

---

## 1. System Overview

### What is PSIA?

PSIA is an **automated multi-agent ML system** that:
1. Fetches daily financial news for stocks in user portfolios
2. Analyzes sentiment using FinBERT (financial-domain BERT model)
3. Generates actionable summaries using LLMs
4. Calculates portfolio risk based on weighted sentiment
5. Delivers email reports before market open

### Key Technologies

| Component | Technology |
|-----------|------------|
| Orchestration | LangGraph (state machine) |
| Sentiment Analysis | FinBERT (HuggingFace Transformers) |
| Summarization | OpenRouter / Anthropic / OpenAI |
| Database | PostgreSQL (SQLAlchemy ORM) |
| Frontend | Streamlit |
| News APIs | NewsAPI + Finnhub |
| Email | SendGrid |
| Containerization | Docker |
| Scheduling | GitHub Actions / Airflow |

### High-Level Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   User       │────▶│  Streamlit   │────▶│  PostgreSQL  │
│  (Browser)   │     │  Frontend    │     │  Database    │
└──────────────┘     └──────────────┘     └──────────────┘
                                                 │
                                                 ▼
┌──────────────────────────────────────────────────────────────┐
│                    PIPELINE EXECUTION                        │
│  ┌─────────┐   ┌─────────┐   ┌──────────┐   ┌─────────────┐ │
│  │Portfolio│──▶│  News   │──▶│Sentiment │──▶│Summarization│ │
│  │ Agent   │   │ Agent   │   │  Agent   │   │   Agent     │ │
│  └─────────┘   └─────────┘   └──────────┘   └─────────────┘ │
│       │                                            │        │
│       │            ┌─────────┐   ┌─────────┐       │        │
│       └───────────▶│  Risk   │──▶│  Email  │◀──────┘        │
│                    │ Agent   │   │  Agent  │                │
│                    └─────────┘   └─────────┘                │
└──────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
                              ┌──────────────────┐
                              │  User's Inbox    │
                              │  (Email Report)  │
                              └──────────────────┘
```

---

## 2. Architecture Deep Dive

### Component Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Streamlit Web App (app/streamlit_app.py)               │   │
│  │  - User registration/login                              │   │
│  │  - Portfolio management (add/remove stocks)             │   │
│  │  - Weight configuration                                 │   │
│  │  - Manual pipeline trigger                              │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     ORCHESTRATION LAYER                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  LangGraph Orchestrator (agents/orchestrator.py)        │   │
│  │  - Defines state machine graph                          │   │
│  │  - Manages pipeline state transitions                   │   │
│  │  - Handles errors and retries                           │   │
│  │  - Logs pipeline execution                              │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        AGENT LAYER                              │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐   │
│  │ Portfolio │  │   News    │  │ Sentiment │  │  Summary  │   │
│  │   Agent   │  │   Agent   │  │   Agent   │  │   Agent   │   │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘   │
│  ┌───────────┐  ┌───────────┐                                  │
│  │   Risk    │  │   Email   │                                  │
│  │   Agent   │  │   Agent   │                                  │
│  └───────────┘  └───────────┘                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       SERVICE LAYER                             │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐   │
│  │  NewsAPI  │  │  Finnhub  │  │    LLM    │  │ SendGrid  │   │
│  │  Service  │  │  Service  │  │  Service  │  │  Service  │   │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘   │
│  ┌───────────────────────────┐  ┌───────────────────────────┐  │
│  │  Sentiment Aggregator     │  │  Portfolio Manager        │  │
│  └───────────────────────────┘  └───────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  PostgreSQL Database                                    │   │
│  │  Tables: users, portfolio, articles, sentiment_scores,  │   │
│  │          portfolio_sentiment, email_log, pipeline_runs  │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  SQLAlchemy ORM (db/models.py)                          │   │
│  │  Connection Pool (db/connection.py)                     │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### LangGraph State Machine

The orchestrator uses LangGraph to define a **directed acyclic graph (DAG)** of agent nodes:

```python
# Simplified graph definition
workflow = StateGraph(PipelineState)

# Add nodes (each node is an agent)
workflow.add_node("portfolio", self._portfolio_node)
workflow.add_node("news", self._news_node)
workflow.add_node("sentiment", self._sentiment_node)
workflow.add_node("aggregate", self._aggregate_node)
workflow.add_node("summarization", self._summarization_node)
workflow.add_node("risk", self._risk_node)
workflow.add_node("email", self._email_node)

# Define edges (execution order)
workflow.set_entry_point("portfolio")
workflow.add_edge("portfolio", "news")
workflow.add_edge("news", "sentiment")
workflow.add_edge("sentiment", "aggregate")
workflow.add_edge("aggregate", "summarization")
workflow.add_edge("summarization", "risk")
workflow.add_edge("risk", "email")
workflow.add_edge("email", END)
```

**Visual representation:**

```
START
  │
  ▼
┌──────────────┐
│  PORTFOLIO   │  Fetch user's portfolio from DB
└──────────────┘
  │
  ▼
┌──────────────┐
│    NEWS      │  Fetch articles from NewsAPI + Finnhub
└──────────────┘
  │
  ▼
┌──────────────┐
│  SENTIMENT   │  Run FinBERT inference on articles
└──────────────┘
  │
  ▼
┌──────────────┐
│  AGGREGATE   │  Calculate weighted sentiment per ticker
└──────────────┘
  │
  ▼
┌──────────────┐
│SUMMARIZATION │  Generate LLM summaries per ticker
└──────────────┘
  │
  ▼
┌──────────────┐
│    RISK      │  Assess portfolio risk level
└──────────────┘
  │
  ▼
┌──────────────┐
│    EMAIL     │  Format and send email report
└──────────────┘
  │
  ▼
 END
```

---

## 3. Multi-Agent System

### Agent Base Class

All agents inherit from `BaseAgent`:

```python
# agents/base_agent.py
class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(name)

    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent logic."""
        pass

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run with logging and timing."""
        self.logger.info(f"Starting {self.name}")
        start_time = time.time()
        result = self.execute(input_data)
        elapsed = time.time() - start_time
        self.logger.info(f"Completed {self.name} in {elapsed:.2f}s")
        return result
```

### Agent Descriptions

#### 1. Portfolio Agent (`agents/portfolio_agent.py`)

**Purpose:** Fetch user's portfolio (tickers + weights) from database.

**Input:**
```python
{
    "user_id": 1
}
```

**Output:**
```python
{
    "portfolio": {
        "AAPL": 0.4,
        "MSFT": 0.3,
        "GOOGL": 0.3
    },
    "user_id": 1
}
```

**Logic:**
1. Query `portfolio` table for user_id
2. Build dictionary of ticker → weight
3. Validate weights sum to 1.0 (or normalize)

---

#### 2. News Agent (`agents/news_agent.py`)

**Purpose:** Fetch financial news articles for each ticker.

**Input:**
```python
{
    "tickers": ["AAPL", "MSFT", "GOOGL"]
}
```

**Output:**
```python
{
    "articles_by_ticker": {
        "AAPL": [
            {
                "headline": "Apple announces new iPhone",
                "content": "Apple Inc. unveiled...",
                "source": "Reuters",
                "url": "https://...",
                "published_at": "2025-12-28T10:00:00Z",
                "ticker": "AAPL"
            },
            ...
        ],
        "MSFT": [...],
        "GOOGL": [...]
    }
}
```

**Logic:**
1. For each ticker (in parallel using ThreadPoolExecutor):
   - Fetch from NewsAPI (primary)
   - If < 3 articles, fallback to Finnhub
   - Merge results, deduplicate by URL
2. Store articles in database with content hash
3. Return ArticleData objects

**Deduplication:**
- Uses SHA-256 hash of `headline + source` as content_hash
- Prevents storing duplicate articles

---

#### 3. Sentiment Agent (`agents/sentiment_agent.py`)

**Purpose:** Analyze sentiment of articles using FinBERT.

**Input:**
```python
{
    "articles": [ArticleData, ArticleData, ...]
}
```

**Output:**
```python
{
    "sentiments": [
        {
            "article_id": 1,
            "label": "positive",
            "confidence": 0.87,
            "score": 1.0
        },
        {
            "article_id": 2,
            "label": "negative",
            "confidence": 0.92,
            "score": -1.0
        },
        ...
    ]
}
```

**Logic:**
1. Load FinBERT model (cached after first load)
2. Prepare text: `headline + content[:500]`
3. Batch inference (default batch_size=8)
4. For each article:
   - Get scores for positive/negative/neutral
   - Select label with highest score
   - Map to score: positive=+1.0, negative=-1.0, neutral=0.0
5. Store sentiment in database

---

#### 4. Aggregation Node (in orchestrator)

**Purpose:** Calculate weighted sentiment per ticker.

**Formula:**
```
weighted_sentiment = Σ(sentiment_score × combined_weight) / Σ(combined_weight)

where:
combined_weight = recency_weight × credibility_weight × confidence
```

**Recency Weights:**
| Age | Weight |
|-----|--------|
| 0-6 hours | 1.0 |
| 6-12 hours | 0.8 |
| 12-24 hours | 0.6 |
| >24 hours | 0.0 |

**Credibility Weights:**
| Source | Weight |
|--------|--------|
| Reuters | 1.0 |
| Bloomberg | 0.95 |
| CNBC | 0.85 |
| Default | 0.6 |

---

#### 5. Summarization Agent (`agents/summarization_agent.py`)

**Purpose:** Generate human-readable summaries per ticker using LLM.

**Input:**
```python
{
    "ticker_data": {
        "AAPL": {
            "articles": [...],
            "sentiments": [...]
        }
    }
}
```

**Output:**
```python
{
    "summaries_by_ticker": {
        "AAPL": "Apple (AAPL) shows positive momentum following strong iPhone sales...",
        "MSFT": "Microsoft (MSFT) faces mixed sentiment due to regulatory concerns..."
    }
}
```

**Prompt Template:**
```
Analyze the following financial news articles about {ticker} and provide 
a concise 2-3 sentence summary.

Focus on:
1. The cause (what happened) and its impact on the company
2. Explicitly mention the company name ({ticker})
3. The overall sentiment trend (improving/declining/stable)
4. Avoid hype language, be factual

Sentiment Analysis Summary:
{sentiment_summary}

Articles:
{articles_text}

Provide a clear, actionable financial summary:
```

---

#### 6. Risk Agent (`agents/risk_agent.py`)

**Purpose:** Assess portfolio risk based on sentiment data.

**Input:**
```python
{
    "portfolio": {"AAPL": 0.4, "MSFT": 0.3, "GOOGL": 0.3},
    "ticker_sentiments": {"AAPL": 0.8, "MSFT": -0.2, "GOOGL": 0.3},
    "ticker_confidences": {"AAPL": 0.87, "MSFT": 0.92, "GOOGL": 0.75}
}
```

**Output:**
```python
{
    "portfolio_sentiment": 0.31,
    "risk_level": "low",
    "signal": "hold",
    "reason": "Portfolio sentiment is stable with low risk indicators.",
    "ticker_risks": {
        "AAPL": "low",
        "MSFT": "medium",
        "GOOGL": "low"
    }
}
```

**Risk Calculation:**
```python
risk_score = |sentiment| × weight × (1 - confidence)
```

- Higher sentiment volatility = higher risk
- Higher portfolio weight = more impact
- Lower confidence = higher uncertainty

**Risk Thresholds:**
| Risk Score | Level | Signal |
|------------|-------|--------|
| < 0.3 | Low | HOLD |
| 0.3 - 0.8 | Medium | MONITOR |
| > 0.8 | High | REVIEW |

---

#### 7. Email Agent (`agents/email_agent.py`)

**Purpose:** Format and send email report via SendGrid.

**Input:**
```python
{
    "user_email": "user@example.com",
    "portfolio": {"AAPL": 0.4, ...},
    "ticker_data": {...},
    "portfolio_risk": "low",
    "date": "2025-12-28"
}
```

**Output:**
```python
{
    "success": True,
    "error_message": None
}
```

**Email Template:**
- HTML formatted report
- Portfolio overview table (ticker, weight, sentiment, risk)
- Summaries per ticker
- Source articles with links
- Risk level indicator

---

## 4. Data Flow & Pipeline

### Complete Pipeline Execution

```
USER TRIGGERS PIPELINE (via main.py --user-id 1)
                    │
                    ▼
┌────────────────────────────────────────────────────────────────────┐
│  STEP 1: PORTFOLIO AGENT                                           │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  Query: SELECT ticker, weight FROM portfolio WHERE user_id=1 │ │
│  │  Result: {AAPL: 0.4, MSFT: 0.3, GOOGL: 0.3}                  │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────────────────────────────┐
│  STEP 2: NEWS AGENT                                                │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  For each ticker (parallel):                                  │ │
│  │    1. NewsAPI: GET /v2/everything?q=AAPL                     │ │
│  │    2. If < 3 articles: Finnhub: GET /company-news?symbol=AAPL│ │
│  │    3. Deduplicate, store in articles table                   │ │
│  │  Result: {AAPL: [5 articles], MSFT: [3 articles], ...}       │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────────────────────────────┐
│  STEP 3: SENTIMENT AGENT                                           │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  Load FinBERT model (ProsusAI/finbert)                       │ │
│  │  For each article batch (size=8):                             │ │
│  │    text = headline + content[:500]                            │ │
│  │    result = model(text)  # Returns {positive, neutral, neg}   │ │
│  │    label = max(result)                                        │ │
│  │  Result: [{label: positive, confidence: 0.87, score: 1.0}...] │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────────────────────────────┐
│  STEP 4: AGGREGATION                                               │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  For each ticker:                                             │ │
│  │    weighted_sum = 0                                           │ │
│  │    for article, sentiment in zip(articles, sentiments):       │ │
│  │      recency = get_recency_weight(article.published_at)       │ │
│  │      credibility = get_source_weight(article.source)          │ │
│  │      weight = recency × credibility × sentiment.confidence    │ │
│  │      weighted_sum += sentiment.score × weight                 │ │
│  │    ticker_sentiment = weighted_sum / total_weight             │ │
│  │  Result: {AAPL: 0.72, MSFT: -0.15, GOOGL: 0.43}              │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────────────────────────────┐
│  STEP 5: SUMMARIZATION AGENT                                       │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  For each ticker:                                             │ │
│  │    prompt = format_prompt(ticker, articles, sentiments)       │ │
│  │    summary = llm_service.summarize(prompt)                    │ │
│  │  Result: {                                                    │ │
│  │    AAPL: "Apple shows strong momentum...",                    │ │
│  │    MSFT: "Microsoft faces regulatory headwinds..."            │ │
│  │  }                                                            │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────────────────────────────┐
│  STEP 6: RISK AGENT                                                │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  portfolio_sentiment = Σ(sentiment × weight) for all tickers │ │
│  │  risk_score = |sentiment| × weight × (1 - confidence)        │ │
│  │  Result: {                                                    │ │
│  │    portfolio_sentiment: 0.31,                                 │ │
│  │    risk_level: "low",                                         │ │
│  │    signal: "hold",                                            │ │
│  │    reason: "Portfolio sentiment is stable..."                 │ │
│  │  }                                                            │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────────────────────────────┐
│  STEP 7: EMAIL AGENT                                               │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  1. Format HTML email with all data                           │ │
│  │  2. SendGrid API: POST /v3/mail/send                         │ │
│  │  3. Log to email_log table                                    │ │
│  │  Result: {success: true}                                      │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
              PIPELINE COMPLETE
```

### Pipeline State Object

Throughout execution, state is passed between nodes:

```python
class PipelineState(TypedDict):
    # User info
    user_id: int
    user_email: str
    
    # Portfolio data
    portfolio: Dict[str, float]  # {ticker: weight}
    
    # News data
    articles_by_ticker: Dict[str, List[ArticleData]]
    
    # Sentiment data
    sentiments_by_article: Dict[str, List[SentimentResult]]
    ticker_sentiments: Dict[str, float]      # Aggregated scores
    ticker_confidences: Dict[str, float]     # Average confidence
    
    # Summaries
    summaries_by_ticker: Dict[str, str]
    
    # Risk assessment
    risk_assessment: Dict[str, Any]
    
    # Email status
    email_sent: bool
    error: str | None
    pipeline_run_id: int | None
```

---

## 5. Database Schema

### Entity Relationship Diagram

```
┌─────────────────┐     ┌─────────────────────┐
│     users       │     │     portfolio       │
├─────────────────┤     ├─────────────────────┤
│ id (PK)         │◄────│ id (PK)             │
│ email           │     │ user_id (FK)        │
│ created_at      │     │ ticker              │
└─────────────────┘     │ weight              │
        │               │ updated_at          │
        │               └─────────────────────┘
        │
        │               ┌─────────────────────┐
        │               │     articles        │
        │               ├─────────────────────┤
        │               │ id (PK)             │
        │               │ ticker              │
        │               │ headline            │
        │               │ content             │
        │               │ source              │
        │               │ url                 │
        │               │ published_at        │
        │               │ content_hash        │◄───────┐
        │               │ created_at          │        │
        │               └─────────────────────┘        │
        │                       │                      │
        │                       ▼                      │
        │               ┌─────────────────────┐        │
        │               │  sentiment_scores   │        │
        │               ├─────────────────────┤        │
        │               │ id (PK)             │        │
        │               │ article_id (FK)     │────────┘
        │               │ label               │
        │               │ confidence          │
        │               │ score               │
        │               │ model_version       │
        │               │ created_at          │
        │               └─────────────────────┘
        │
        ▼
┌─────────────────────┐     ┌─────────────────────┐
│ portfolio_sentiment │     │     email_log       │
├─────────────────────┤     ├─────────────────────┤
│ id (PK)             │     │ id (PK)             │
│ user_id (FK)        │     │ user_id (FK)        │
│ date                │     │ sent_at             │
│ ticker              │     │ status              │
│ sentiment_score     │     │ error_message       │
│ article_count       │     └─────────────────────┘
│ avg_confidence      │
│ created_at          │     ┌─────────────────────┐
└─────────────────────┘     │   pipeline_runs     │
                            ├─────────────────────┤
                            │ id (PK)             │
                            │ user_id (FK)        │
                            │ started_at          │
                            │ completed_at        │
                            │ status              │
                            │ error_message       │
                            │ execution_time_secs │
                            └─────────────────────┘
```

### Table Definitions

#### `users`
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `portfolio`
```sql
CREATE TABLE portfolio (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ticker VARCHAR(10) NOT NULL,
    weight DECIMAL(5, 4) NOT NULL CHECK (weight >= 0 AND weight <= 1),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, ticker)
);
```
- `weight` is stored as decimal (0.0000 to 1.0000)
- Unique constraint ensures no duplicate tickers per user

#### `articles`
```sql
CREATE TABLE articles (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    headline TEXT NOT NULL,
    content TEXT NOT NULL,
    source VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    published_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    content_hash VARCHAR(64) UNIQUE
);
```
- `content_hash` = SHA-256(headline + source) for deduplication

#### `sentiment_scores`
```sql
CREATE TABLE sentiment_scores (
    id SERIAL PRIMARY KEY,
    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    label VARCHAR(20) NOT NULL CHECK (label IN ('positive', 'neutral', 'negative')),
    confidence DECIMAL(5, 4) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    score DECIMAL(5, 4) NOT NULL CHECK (score >= -1 AND score <= 1),
    model_version VARCHAR(50) DEFAULT 'ProsusAI/finbert',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 6. Frontend (Streamlit)

### Application Structure

```
app/
├── streamlit_app.py    # Main application file
└── run.sh              # Startup script
```

### Pages/Views

#### 1. Login/Registration

```
┌─────────────────────────────────────────────────────────────┐
│  📊 Portfolio Sentiment Agent                               │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  SIDEBAR                                            │   │
│  │  ────────────────────────────────────────────────── │   │
│  │  Access Account                                     │   │
│  │                                                     │   │
│  │  Email: [_______________]                           │   │
│  │                                                     │   │
│  │  [   Login   ]   [  Register  ]                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Welcome! Please log in or register to manage your          │
│  portfolio.                                                 │
└─────────────────────────────────────────────────────────────┘
```

#### 2. Dashboard (After Login)

```
┌─────────────────────────────────────────────────────────────┐
│  📊 Portfolio Sentiment Agent                               │
│                                                             │
│  ┌───────────────┐  ┌───────────────────────────────────┐  │
│  │  SIDEBAR      │  │  MAIN CONTENT                     │  │
│  │  ───────────  │  │  ─────────────────────────────    │  │
│  │               │  │                                   │  │
│  │  Logged in:   │  │  📈 Your Portfolio                │  │
│  │  user@mail    │  │                                   │  │
│  │               │  │  ┌─────────────────────────────┐  │  │
│  │  [Dashboard]  │  │  │ Ticker │ Weight │ Actions  │  │  │
│  │  [Add Stocks] │  │  │────────│────────│──────────│  │  │
│  │  [Settings]   │  │  │ AAPL   │ 40%    │ [Remove] │  │  │
│  │  [History]    │  │  │ MSFT   │ 30%    │ [Remove] │  │  │
│  │               │  │  │ GOOGL  │ 30%    │ [Remove] │  │  │
│  │  ───────────  │  │  └─────────────────────────────┘  │  │
│  │  [Run Now]    │  │                                   │  │
│  │  [Logout]     │  │  Total: 100% ✓                    │  │
│  └───────────────┘  └───────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

#### 3. Add Stocks

```
┌─────────────────────────────────────────────────────────────┐
│  ➕ Add Stocks                                              │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Manual Entry                                       │   │
│  │                                                     │   │
│  │  Ticker: [AAPL    ]  Weight: [0.4  ]               │   │
│  │                                                     │   │
│  │  [   Add to Portfolio   ]                          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Quick Add (10% weight each)                        │   │
│  │                                                     │   │
│  │  [+AAPL] [+MSFT] [+GOOGL] [+AMZN] [+TSLA]         │   │
│  │  [+META] [+NVDA] [+JPM]   [+V]    [+JNJ]          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Bulk Import (CSV format)                           │   │
│  │                                                     │   │
│  │  ┌─────────────────────────────────────────────┐   │   │
│  │  │ AAPL,0.4                                    │   │   │
│  │  │ MSFT,0.3                                    │   │   │
│  │  │ GOOGL,0.3                                   │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  │                                                     │   │
│  │  [   Import   ]                                    │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

#### 4. Settings

```
┌─────────────────────────────────────────────────────────────┐
│  ⚙️ Settings                                                │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Weight Management                                  │   │
│  │                                                     │   │
│  │  Current total: 90% ⚠️                              │   │
│  │                                                     │   │
│  │  [  Normalize Weights to 100%  ]                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Adjust Individual Weights                          │   │
│  │                                                     │   │
│  │  AAPL: [====|========] 0.40                        │   │
│  │  MSFT: [===|=========] 0.30                        │   │
│  │  GOOGL:[===|=========] 0.30                        │   │
│  │                                                     │   │
│  │  [   Save Changes   ]                              │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Session State Management

```python
# Streamlit session state
st.session_state = {
    "logged_in": True,
    "user": {
        "id": 1,
        "email": "user@example.com"
    },
    "page": "dashboard"  # or "add_stocks", "settings", "history"
}
```

---

## 7. External Services & APIs

### NewsAPI

**Base URL:** `https://newsapi.org/v2`

**Endpoint:** `/everything`

**Parameters:**
| Parameter | Value | Description |
|-----------|-------|-------------|
| q | `AAPL` | Stock ticker |
| from | `2025-12-27` | Start date (24h ago) |
| language | `en` | English only |
| sortBy | `publishedAt` | Most recent first |
| pageSize | `5` | Max articles per request |

**Response:**
```json
{
  "articles": [
    {
      "title": "Apple Stock Rises on...",
      "description": "Apple Inc. saw gains...",
      "source": {"name": "Reuters"},
      "url": "https://...",
      "publishedAt": "2025-12-28T10:00:00Z",
      "content": "Full article content..."
    }
  ]
}
```

**Limitations (Free Tier):**
- 100 requests/day
- 1 month history
- No company-specific filtering

---

### Finnhub

**Base URL:** `https://finnhub.io/api/v1`

**Endpoint:** `/company-news`

**Parameters:**
| Parameter | Value |
|-----------|-------|
| symbol | `AAPL` |
| from | `2025-12-27` |
| to | `2025-12-28` |

**Response:**
```json
[
  {
    "headline": "Apple announces...",
    "summary": "Summary text...",
    "source": "Yahoo Finance",
    "url": "https://...",
    "datetime": 1735387200
  }
]
```

**Limitations (Free Tier):**
- 60 requests/minute
- 1 year history

---

### SendGrid

**Base URL:** `https://api.sendgrid.com/v3`

**Endpoint:** `/mail/send`

**Payload:**
```json
{
  "personalizations": [
    {
      "to": [{"email": "user@example.com"}],
      "subject": "Portfolio Sentiment Report - 2025-12-28"
    }
  ],
  "from": {
    "email": "reports@yourdomain.com",
    "name": "Portfolio Sentiment Agent"
  },
  "content": [
    {
      "type": "text/html",
      "value": "<html>...</html>"
    }
  ]
}
```

---

### OpenRouter (LLM)

**Base URL:** `https://openrouter.ai/api/v1`

**Endpoint:** `/chat/completions`

**Model:** `allenai/olmo-3.1-32b-think:free`

**Request:**
```json
{
  "model": "allenai/olmo-3.1-32b-think:free",
  "messages": [
    {"role": "user", "content": "Analyze..."}
  ],
  "max_tokens": 200,
  "temperature": 0.3
}
```

**Free Tier:** Unlimited (rate-limited)

---

## 8. ML Components

### FinBERT Model

**Model:** `ProsusAI/finbert`

**Architecture:** BERT-base with financial domain fine-tuning

**Classes:** `positive`, `neutral`, `negative`

**Input Processing:**
```python
# Combine headline and content
text = f"{headline} {content[:500]}"

# Tokenize
tokens = tokenizer(
    text,
    padding=True,
    truncation=True,
    max_length=512,
    return_tensors="pt"
)
```

**Inference:**
```python
with torch.no_grad():
    outputs = model(**tokens)
    probabilities = torch.softmax(outputs.logits, dim=-1)
    
# probabilities = [[0.1, 0.2, 0.7]]  # [negative, neutral, positive]
```

**Score Mapping:**
```python
label_to_score = {
    "positive": 1.0,
    "neutral": 0.0,
    "negative": -1.0
}
```

### Model Loading (Lazy)

```python
class SentimentAgent:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        
    def _load_model(self):
        if self.model is None:
            self.tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
            self.model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
            self.model.eval()
```

---

## 9. Sentiment Aggregation Algorithm

### Mathematical Formula

For each ticker:

```
weighted_sentiment = Σ(Si × Wi) / Σ(Wi)

where:
Si = sentiment score for article i (-1 to +1)
Wi = combined weight for article i

Wi = Ri × Ci × Fi

where:
Ri = recency weight (time decay)
Ci = credibility weight (source trust)
Fi = confidence weight (model certainty)
```

### Example Calculation

**Inputs:**
| Article | Source | Age | Sentiment | Confidence |
|---------|--------|-----|-----------|------------|
| 1 | Reuters | 2h | +1.0 | 0.92 |
| 2 | CNBC | 8h | -1.0 | 0.78 |
| 3 | Blog | 20h | +1.0 | 0.85 |

**Weights:**
| Article | Recency | Credibility | Confidence | Combined |
|---------|---------|-------------|------------|----------|
| 1 | 1.0 | 1.0 | 0.92 | 0.92 |
| 2 | 0.8 | 0.85 | 0.78 | 0.53 |
| 3 | 0.6 | 0.60 | 0.85 | 0.31 |

**Calculation:**
```
weighted_sum = (1.0 × 0.92) + (-1.0 × 0.53) + (1.0 × 0.31)
             = 0.92 - 0.53 + 0.31
             = 0.70

total_weight = 0.92 + 0.53 + 0.31 = 1.76

weighted_sentiment = 0.70 / 1.76 = 0.40
```

**Result:** AAPL sentiment = +0.40 (slightly positive)

---

## 10. Risk Assessment Logic

### Per-Ticker Risk

```python
def calculate_ticker_risk(sentiment, weight, confidence):
    """
    Higher risk when:
    - Sentiment is extreme (very positive or very negative)
    - Stock has high portfolio weight
    - Model confidence is low (uncertainty)
    """
    risk_score = abs(sentiment) * weight * (1 - confidence)
    
    if risk_score < 0.3:
        return "low"
    elif risk_score < 0.8:
        return "medium"
    else:
        return "high"
```

### Portfolio-Level Risk

```python
portfolio_sentiment = sum(
    ticker_sentiment * portfolio_weight
    for ticker in portfolio
)

# Aggregated risk
avg_risk = sum(
    abs(sentiment) * weight * (1 - confidence)
    for ticker in portfolio
)

if avg_risk < 0.3:
    risk_level = "LOW"
    signal = "HOLD"
    reason = "Portfolio sentiment is stable..."
elif avg_risk < 0.8:
    risk_level = "MEDIUM"
    signal = "MONITOR"
    reason = "Moderate volatility detected..."
else:
    risk_level = "HIGH"
    signal = "REVIEW"
    reason = "High risk - consider rebalancing..."
```

### Risk Matrix

```
                    LOW CONFIDENCE       HIGH CONFIDENCE
                    (uncertainty)        (certainty)
    ┌───────────────┬───────────────────┬───────────────────┐
    │               │                   │                   │
 H  │  VERY HIGH    │    HIGH           │    MEDIUM         │
 I  │  RISK         │    RISK           │    RISK           │
 G  │               │                   │                   │
 H  │  ⚠️ Review     │   ⚠️ Review        │   👀 Monitor       │
    ├───────────────┼───────────────────┼───────────────────┤
 S  │               │                   │                   │
 E  │  HIGH         │    MEDIUM         │    LOW            │
 N  │  RISK         │    RISK           │    RISK           │
 T  │               │                   │                   │
 I  │  ⚠️ Review     │   👀 Monitor       │   ✅ Hold          │
 M  ├───────────────┼───────────────────┼───────────────────┤
 E  │               │                   │                   │
 N  │  MEDIUM       │    LOW            │    VERY LOW       │
 T  │  RISK         │    RISK           │    RISK           │
    │               │                   │                   │
 L  │  👀 Monitor    │   ✅ Hold          │   ✅ Hold          │
 O  │               │                   │                   │
 W  └───────────────┴───────────────────┴───────────────────┘
```

---

## 11. Configuration Management

### Environment Variables (.env)

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/portfolio_sentiment

# API Keys
NEWSAPI_KEY=your_newsapi_key
FINNHUB_KEY=your_finnhub_key
SENDGRID_API_KEY=your_sendgrid_key

# LLM Configuration
LLM_PROVIDER=openrouter
LLM_KEY=your_openrouter_key
OPENROUTER_MODEL=allenai/olmo-3.1-32b-think:free

# Email
EMAIL_FROM=reports@yourdomain.com

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Settings Class

```python
class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # API Keys
    NEWSAPI_KEY: str
    FINNHUB_KEY: str
    SENDGRID_API_KEY: str
    
    # LLM
    LLM_PROVIDER: Literal["anthropic", "openai", "openrouter"]
    LLM_KEY: str | None
    OPENROUTER_MODEL: str = "allenai/olmo-3.1-32b-think:free"
    
    # Model Config
    SENTIMENT_MODEL: str = "ProsusAI/finbert"
    SENTIMENT_BATCH_SIZE: int = 8
    
    # Risk Thresholds
    RISK_THRESHOLD_LOW: float = 0.3
    RISK_THRESHOLD_HIGH: float = 0.8
    
    # News Config
    NEWS_TIME_WINDOW_HOURS: int = 24
    NEWS_MAX_ARTICLES_PER_TICKER: int = 5
    
    # Source Weights
    SOURCE_WEIGHT_REUTERS: float = 1.0
    SOURCE_WEIGHT_BLOOMBERG: float = 0.95
    SOURCE_WEIGHT_CNBC: float = 0.85
    SOURCE_WEIGHT_DEFAULT: float = 0.6
    
    class Config:
        env_file = ".env"
```

### Configuration Hierarchy

```
Priority (highest to lowest):
1. Environment variables
2. .env file
3. Google Cloud Secret Manager (if GCP_PROJECT_ID set)
4. Default values in Settings class
```

---

## 12. Deployment Options

### Option 1: Local Development

```bash
# 1. Start PostgreSQL
docker-compose up -d postgres

# 2. Run Streamlit
streamlit run app/streamlit_app.py

# 3. Run pipeline manually
python main.py --user-id 1
```

### Option 2: GitHub Actions (Free)

```yaml
# .github/workflows/daily_sentiment.yml
name: Daily Sentiment Pipeline

on:
  schedule:
    - cron: '30 12 * * 1-5'  # 6:30 AM EST weekdays
  workflow_dispatch:

jobs:
  run-pipeline:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run pipeline
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          NEWSAPI_KEY: ${{ secrets.NEWSAPI_KEY }}
          # ... other secrets
        run: python scripts/run_pipeline.py
```

### Option 3: Google Cloud Composer (Airflow)

```python
# airflow/dags/portfolio_sentiment_dag.py
from airflow import DAG
from airflow.operators.python import PythonOperator

with DAG(
    'portfolio_sentiment_pipeline',
    schedule_interval='30 12 * * 1-5',  # 6:30 AM EST
    catchup=False,
) as dag:
    
    run_pipeline = PythonOperator(
        task_id='run_pipeline',
        python_callable=run_all_users_pipeline,
    )
```

### Option 4: Docker Compose (Full Stack)

```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: portfolio_sentiment
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  streamlit:
    build: .
    ports:
      - "8501:8501"
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/portfolio_sentiment
    depends_on:
      - postgres
    command: streamlit run app/streamlit_app.py
```

### Deployment Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PRODUCTION DEPLOYMENT                        │
│                                                                     │
│  ┌─────────────────┐     ┌─────────────────┐     ┌──────────────┐  │
│  │  Streamlit      │     │  GitHub Actions │     │  Supabase    │  │
│  │  Community      │────▶│  (Scheduler)    │────▶│  PostgreSQL  │  │
│  │  Cloud          │     │                 │     │              │  │
│  │                 │     │  OR             │     │  OR          │  │
│  │  OR Render      │     │                 │     │              │  │
│  │  OR Railway     │     │  Cloud Composer │     │  RDS Aurora  │  │
│  │  OR Vercel      │     │  (Airflow)      │     │              │  │
│  └─────────────────┘     └─────────────────┘     └──────────────┘  │
│          │                       │                      │          │
│          │                       ▼                      │          │
│          │               ┌──────────────┐               │          │
│          └──────────────▶│    APIs      │◀──────────────┘          │
│                          │  - NewsAPI   │                          │
│                          │  - Finnhub   │                          │
│                          │  - OpenRouter│                          │
│                          │  - SendGrid  │                          │
│                          └──────────────┘                          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 13. File Structure Reference

```
portfolio-sentiment-agent/
│
├── agents/                      # Multi-agent system
│   ├── __init__.py
│   ├── base_agent.py           # Abstract base class
│   ├── portfolio_agent.py      # Fetches user portfolios
│   ├── news_agent.py           # Fetches financial news
│   ├── sentiment_agent.py      # FinBERT inference
│   ├── summarization_agent.py  # LLM summaries
│   ├── risk_agent.py           # Risk assessment
│   ├── email_agent.py          # Email formatting/sending
│   ├── orchestrator.py         # LangGraph pipeline
│   └── schemas.py              # Pydantic input/output contracts
│
├── app/                        # Frontend
│   ├── __init__.py
│   ├── streamlit_app.py        # Streamlit web application
│   └── run.sh                  # Startup script
│
├── config/                     # Configuration
│   ├── __init__.py
│   ├── settings.py             # Pydantic settings
│   ├── logging_config.py       # Logging setup
│   └── portfolios.yaml         # Sample portfolios
│
├── db/                         # Database
│   ├── __init__.py
│   ├── connection.py           # SQLAlchemy engine
│   ├── models.py               # ORM models
│   ├── schema.sql              # Raw SQL schema
│   └── migrations/             # Database migrations
│
├── services/                   # External service integrations
│   ├── __init__.py
│   ├── news_api.py             # NewsAPI client
│   ├── finnhub_api.py          # Finnhub client
│   ├── llm_service.py          # LLM abstraction (OpenRouter/Anthropic/OpenAI)
│   ├── email_service.py        # SendGrid client
│   ├── portfolio_manager.py    # Portfolio CRUD operations
│   └── sentiment_aggregator.py # Aggregation logic
│
├── scripts/                    # Utility scripts
│   ├── run_pipeline.py         # Run for all users
│   ├── setup_example_user.py   # Create demo user
│   └── seed_users.py           # Seed database
│
├── tests/                      # Test suite
│   ├── conftest.py             # Pytest fixtures
│   ├── test_portfolio_agent.py
│   ├── test_news_agent.py
│   └── test_portfolio_manager.py
│
├── airflow/                    # Airflow deployment
│   ├── dags/
│   │   └── portfolio_sentiment_dag.py
│   └── README.md
│
├── docs/                       # Documentation
│   ├── architecture.md
│   └── TECHNICAL_DOCUMENTATION.md  # This file
│
├── .env.example                # Environment template
├── .gitignore
├── docker-compose.yml          # Local development
├── Dockerfile                  # Container image
├── main.py                     # CLI entry point
├── requirements.txt            # Python dependencies
├── pyproject.toml              # Project metadata
└── README.md                   # Quick start guide
```

---

## Quick Reference Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Start local PostgreSQL
docker-compose up -d postgres

# Initialize database
python -c "from db import db_manager; db_manager.create_tables()"

# Run Streamlit app
streamlit run app/streamlit_app.py

# Run pipeline for user
python main.py --user-id 1

# Run pipeline for all users
python scripts/run_pipeline.py

# Run tests
pytest tests/ -v
```

---

## Troubleshooting

### No articles fetched
- NewsAPI free tier has limited requests (100/day)
- Try more popular stocks (AAPL, MSFT, GOOGL)
- Check if it's a weekend (less financial news)

### Database connection errors
- Ensure PostgreSQL is running
- Check DATABASE_URL format
- Verify credentials

### LLM API errors
- Check LLM_KEY is set correctly
- Verify LLM_PROVIDER matches the key
- OpenRouter free tier is rate-limited

### Email not sending
- Verify SENDGRID_API_KEY
- Check EMAIL_FROM is verified in SendGrid
- Review email_log table for errors

---

*Last updated: December 28, 2025*

