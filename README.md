# Portfolio Sentiment Intelligence Agent

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Live Demo](https://img.shields.io/badge/demo-live-success)](https://portfolio-sentiment-agent-bdssllsd9euqhwrpctccrs.streamlit.app/)

> **An AI-powered multi-agent system that automates financial sentiment analysis and delivers actionable portfolio insights before market open**

🔗 **[Live Demo](https://portfolio-sentiment-agent-bdssllsd9euqhwrpctccrs.streamlit.app/)** | 📊 **[View on GitHub](https://github.com/himnishpersonal/portfolio-sentiment-agent)**

## 🎯 Project Overview

This production-grade system leverages **6 specialized AI agents** orchestrated via LangGraph to automatically analyze financial news sentiment and generate portfolio risk assessments. Built with FinBERT transformer (91% confidence) and Meta Llama 3.2 LLM, the pipeline processes real-time news with <3-second latency and delivers automated email reports with color-coded risk indicators.

### Key Features

- ✅ **Multi-Agent Architecture:** 6 specialized agents (Portfolio, News, Sentiment, Summarization, Risk, Email)
- ✅ **AI/ML Integration:** FinBERT NLP (91% confidence) + Meta Llama 3.2 3B for summarization
- ✅ **Real-Time Analysis:** <3 second end-to-end pipeline execution
- ✅ **Automated Deployment:** GitHub Actions with daily scheduling at 6 AM ET
- ✅ **Full-Stack App:** Interactive Streamlit UI + PostgreSQL backend
- ✅ **Production-Ready:** Docker containerization, API integrations, error handling

### Technical Achievements

1. **Architected event-driven multi-agent system** with 6 specialized agents (Portfolio, News, Sentiment, Summarization, Risk, Email) orchestrated via LangGraph, integrating 5 external APIs (NewsAPI, Finnhub, OpenRouter LLM, SendGrid, PostgreSQL) for automated financial analysis pipeline

2. **Leveraged FinBERT transformer** (91% classification confidence) and Meta Llama 3.2 3B for sentiment analysis and summarization, implementing custom weighted scoring algorithms with recency decay, source credibility scoring (Reuters, Bloomberg, CNBC), and confidence-based portfolio risk assessment

3. **Built containerized deployment architecture** with Docker/Docker Compose for cloud deployment on GitHub Actions with automated daily execution, Supabase PostgreSQL backend, and Streamlit web interface for real-time portfolio management

## 📊 System Metrics

| Metric | Value |
|--------|-------|
| **AI Agents** | 6 specialized agents |
| **API Integrations** | 5 external services |
| **ML Confidence** | 91% (FinBERT) |
| **Pipeline Latency** | <3 seconds |
| **Deployment** | GitHub Actions + Streamlit Cloud |
| **Database** | PostgreSQL (Supabase) |

## 🏗️ Architecture

```mermaid
graph TD
    A[Orchestrator] --> B[Portfolio Agent]
    B --> C[News Agent]
    C --> D[Sentiment Agent]
    D --> E[Aggregation]
    E --> F[Summarization Agent]
    F --> G[Risk Agent]
    G --> H[Email Agent]
    
    C --> I[NewsAPI]
    C --> J[Finnhub]
    D --> K[FinBERT Model]
    F --> L[LLM API]
    H --> M[SendGrid]
```

## 🛠️ Tech Stack

**AI/ML:**
- **NLP Model:** FinBERT (ProsusAI/finbert) - Financial sentiment analysis
- **LLM:** Meta Llama 3.2 3B (via OpenRouter) - News summarization
- **ML Framework:** PyTorch, HuggingFace Transformers
- **Orchestration:** LangGraph - Multi-agent workflow coordination

**Backend:**
- **Language:** Python 3.11
- **Database:** PostgreSQL (Supabase)
- **ORM:** SQLAlchemy
- **APIs:** NewsAPI, Finnhub, OpenRouter, SendGrid

**Frontend & Deployment:**
- **UI:** Streamlit (deployed on Streamlit Cloud)
- **CI/CD:** GitHub Actions (automated daily runs)
- **Containerization:** Docker, Docker Compose
- **Cloud:** Supabase (database), Streamlit Cloud (web app)

## 🎬 Live Demo

**Try it now:** [https://portfolio-sentiment-agent-bdssllsd9euqhwrpctccrs.streamlit.app/](https://portfolio-sentiment-agent-bdssllsd9euqhwrpctccrs.streamlit.app/)

The live application features:
- 📊 **Interactive Dashboard** - View portfolio sentiment in real-time
- ➕ **Portfolio Management** - Add/remove stocks, adjust weights
- 🤖 **One-Click Analysis** - Run sentiment analysis on demand
- 📧 **Email Reports** - Automated daily reports with color-coded risk levels
- 📈 **Run History** - Track analysis performance over time

## 📋 Prerequisites

For local development:
- Python 3.11 or higher
- PostgreSQL database (Supabase recommended)
- API keys (free tiers available):
  - [NewsAPI](https://newsapi.org/) - News articles
  - [Finnhub](https://finnhub.io/) - Financial data
  - [SendGrid](https://sendgrid.com/) - Email delivery
  - [OpenRouter](https://openrouter.ai/) - Free LLM access

## 🚀 Quick Start

### Option 1: Use Live Demo (Fastest)

Visit [https://portfolio-sentiment-agent-bdssllsd9euqhwrpctccrs.streamlit.app/](https://portfolio-sentiment-agent-bdssllsd9euqhwrpctccrs.streamlit.app/) to try the system immediately.

### Option 2: Run Locally

```bash
# Clone repository
git clone https://github.com/himnishpersonal/portfolio-sentiment-agent.git
cd portfolio-sentiment-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/portfolio_sentiment
NEWSAPI_KEY=your_key_here
FINNHUB_KEY=your_key_here
SENDGRID_API_KEY=your_key_here

# LLM Configuration - OpenRouter (FREE!)
LLM_PROVIDER=openrouter
LLM_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=allenai/olmo-3.1-32b-think:free

EMAIL_FROM=your_email@example.com
```

### 3. Initialize Database

```bash
# Create database schema
psql -U postgres -c "CREATE DATABASE portfolio_sentiment;"

# Run schema SQL
psql -U postgres -d portfolio_sentiment -f db/schema.sql
```

Or use Python:

```python
from db.connection import db_manager
from db.models import Base
from sqlalchemy import create_engine
from config.settings import settings

engine = create_engine(settings.DATABASE_URL)
Base.metadata.create_all(engine)
```

### 4. Create Example User

```bash
python scripts/setup_example_user.py
```

Or manually:

```bash
python scripts/seed_users.py add-user --email demo@example.com
python scripts/seed_users.py add-portfolio --email demo@example.com --ticker AAPL --weight 0.5
python scripts/seed_users.py add-portfolio --email demo@example.com --ticker MSFT --weight 0.5
```

## 📖 Usage

### Run Pipeline for Single User

```bash
python main.py --user-id 1
```

### Run Pipeline for All Users

```bash
python scripts/run_pipeline.py
```

### Manage Users and Portfolios

```bash
# List all users
python scripts/seed_users.py list-users

# Add user
python scripts/seed_users.py add-user --email user@example.com

# Add ticker to portfolio
python scripts/seed_users.py add-portfolio --email user@example.com --ticker AAPL --weight 0.3

# List user portfolio
python scripts/seed_users.py list-portfolio --email user@example.com

# Update portfolio from JSON file
python scripts/seed_users.py update-portfolio --email user@example.com --file portfolio.json
```

### Load Portfolios from YAML

```bash
python scripts/load_portfolios.py config/portfolios.yaml
```

## 🌐 Web Interface (Streamlit)

A user-friendly web interface for managing portfolios.

### Run Locally

```bash
# Install streamlit if not already
pip install streamlit

# Run the app
streamlit run app/streamlit_app.py

# Or use the run script
./app/run.sh
```

### Features

- **User Registration/Login**: Simple email-based authentication
- **Portfolio Management**: Add, remove, and update stock tickers
- **Quick Add**: Popular stocks with one click
- **Bulk Import**: Import multiple tickers at once
- **Weight Normalization**: Automatically balance portfolio weights
- **Run History**: View recent sentiment analysis runs

### Access

Open http://localhost:8501 in your browser after starting the app.

## 🐳 Docker Deployment

### Build and Run

```bash
docker-compose up --build
```

### Run Pipeline Manually

```bash
docker-compose run app python scripts/run_pipeline.py
```

## 🌐 Production Deployment

**Current Production Setup:**

✅ **Live Application:** [Streamlit Cloud](https://portfolio-sentiment-agent-bdssllsd9euqhwrpctccrs.streamlit.app/)  
✅ **Automated Pipeline:** GitHub Actions (runs daily at 6 AM ET)  
✅ **Database:** Supabase PostgreSQL (managed)  
✅ **Email Delivery:** SendGrid API

### Deployment Architecture

```
User → Streamlit Cloud (UI) → Supabase (Database) ← GitHub Actions (Pipeline)
                                                          ↓
                                                     Email Reports
```

### GitHub Actions Automation

The system automatically runs daily sentiment analysis via GitHub Actions:

1. **Scheduled Execution:** Runs at 6 AM ET every weekday
2. **Manual Trigger:** Can be triggered on-demand from GitHub Actions tab
3. **Multi-User Support:** Processes all registered users' portfolios
4. **Error Handling:** Automatic notifications on pipeline failures

**Setup GitHub Secrets:**
```
DATABASE_URL          - PostgreSQL connection string
NEWSAPI_KEY          - News article fetching
FINNHUB_KEY          - Financial data backup
LLM_KEY              - OpenRouter for summarization
SENDGRID_API_KEY     - Email delivery
```

### Deployment Options

| Option | Best For | Cost | Setup Time |
|--------|----------|------|------------|
| **GitHub Actions + Streamlit Cloud** | MVP, Small Scale | Free | 15 mins ⭐ |
| **Docker Compose** | Local Development | Free | 10 mins |
| **Google Cloud Composer** | Enterprise | ~$300/mo | 2 hours |

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment guides.

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov

# Run specific test file
pytest tests/test_portfolio_agent.py
```

## 📊 ML Validation

Validate sentiment model accuracy:

```bash
# Create labeled headlines file (format: headline|label)
python scripts/validate_sentiment.py labeled_headlines.txt
```

## 🔄 How It Works

```mermaid
graph LR
    A[User Portfolio] --> B[News Agent]
    B --> C[FinBERT<br/>Sentiment]
    C --> D[Llama 3.2<br/>Summary]
    D --> E[Risk<br/>Assessment]
    E --> F[Email<br/>Report]
```

**Pipeline Flow:**

1. **Portfolio Agent** - Fetches user holdings and weights from database
2. **News Agent** - Collects financial news from NewsAPI and Finnhub
3. **Sentiment Agent** - Analyzes sentiment using FinBERT (91% confidence)
4. **Aggregation** - Weights sentiment by recency, source credibility, confidence
5. **Summarization Agent** - Generates readable summaries with Llama 3.2
6. **Risk Agent** - Calculates portfolio risk (LOW/MEDIUM/HIGH)
7. **Email Agent** - Delivers HTML report via SendGrid

## 📁 Project Structure

```
portfolio-sentiment-agent/
├── agents/              # 6 specialized AI agents
├── services/            # API integrations & business logic
├── db/                  # PostgreSQL models & schema
├── config/              # Settings & configuration
├── app/                 # Streamlit web interface
├── scripts/             # Utility scripts
├── tests/               # Test suite
└── .github/workflows/   # GitHub Actions CI/CD
```

## 🔧 Configuration

Key configuration options in `config/settings.py`:

- **Risk Thresholds:** `RISK_THRESHOLD_LOW`, `RISK_THRESHOLD_MEDIUM`, `RISK_THRESHOLD_HIGH`
- **News Settings:** `NEWS_TIME_WINDOW_HOURS`, `NEWS_MAX_ARTICLES_PER_TICKER`
- **Model Settings:** `SENTIMENT_BATCH_SIZE`, `SENTIMENT_MAX_SEQUENCE_LENGTH`
- **Source Credibility:** Weights for different news sources
- **Recency Weights:** How article age affects sentiment weighting

## 📧 Email Report Format

Reports include:
- Portfolio overview table with tickers, weights, and sentiment scores
- Per-ticker summaries with sentiment trends
- Risk level indicators (low/medium/high)
- Links to source articles
- Color-coded risk badges

## 🐛 Troubleshooting

### Database Connection Issues

```bash
# Test database connection
python -c "from db.connection import db_manager; print(db_manager.test_connection())"
```

### API Rate Limits

- NewsAPI: 100 requests/day (free tier)
- Finnhub: 60 calls/minute (free tier)
- Consider upgrading API tiers for production use

### Model Loading Issues

FinBERT model (~500MB) downloads automatically on first use. Ensure sufficient disk space and internet connection.

## 📝 About This Project

This project demonstrates production-grade ML engineering skills including:
- Multi-agent system architecture
- NLP model integration (FinBERT)
- LLM orchestration and prompt engineering
- Real-time data pipeline development
- Cloud deployment and CI/CD
- Full-stack application development

**Built by:** Himnish  
**Contact:** himnish03@gmail.com  
**Live Demo:** [https://portfolio-sentiment-agent-bdssllsd9euqhwrpctccrs.streamlit.app/](https://portfolio-sentiment-agent-bdssllsd9euqhwrpctccrs.streamlit.app/)

## 📝 License

MIT License - feel free to use this project for learning or as a portfolio piece.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/himnishpersonal/portfolio-sentiment-agent/issues).

---

⭐ **If you found this project helpful, please consider giving it a star!**

