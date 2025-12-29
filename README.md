# Portfolio Sentiment Intelligence Agent (PSIA)

A production-ready, automated multi-agent ML system that analyzes daily financial news for user portfolios and delivers actionable sentiment reports before market open.

## 🎯 Overview

PSIA uses a multi-agent architecture to:
1. **Fetch** user portfolio holdings
2. **Collect** relevant financial news articles
3. **Analyze** sentiment using FinBERT (financial BERT model)
4. **Summarize** findings using LLM (Claude/GPT-4)
5. **Assess** portfolio risk levels
6. **Deliver** comprehensive email reports

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

- **Language:** Python 3.11+
- **ML Framework:** PyTorch, HuggingFace Transformers
- **Model:** ProsusAI/finbert for sentiment analysis
- **LLM:** Anthropic Claude or OpenAI GPT-4 for summarization
- **Database:** PostgreSQL (Supabase or RDS)
- **Orchestration:** LangGraph for workflow management
- **APIs:** NewsAPI, Finnhub, SendGrid
- **Deployment:** Docker, GitHub Actions

## 📋 Prerequisites

- Python 3.11 or higher
- PostgreSQL database (local or cloud)
- API keys for:
  - NewsAPI (https://newsapi.org/)
  - Finnhub (https://finnhub.io/)
  - SendGrid (https://sendgrid.com/)
  - Anthropic or OpenAI

## 🚀 Setup

### 1. Clone and Install

```bash
git clone <repository-url>
cd portfolio-sentiment-agent
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
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

## 🔄 Automated Deployment

### Option 1: Google Cloud Composer (Airflow) - Recommended for Production

Deploy to Google Cloud Composer for a fully managed Airflow environment.

**Quick Start:**
```bash
# See DEPLOYMENT.md for full instructions
./airflow/deploy.sh
```

**Features:**
- Fully managed Airflow environment
- Automatic scaling
- Built-in monitoring and logging
- Secure secret management
- Production-ready infrastructure

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete setup instructions.

### Option 2: GitHub Actions (MVP)

The pipeline can also run automatically via GitHub Actions.

**Setup GitHub Secrets:**
- `DATABASE_URL`
- `NEWSAPI_KEY`
- `FINNHUB_KEY`
- `SENDGRID_API_KEY`
- `LLM_PROVIDER`
- `ANTHROPIC_API_KEY` (or `OPENAI_API_KEY`)
- `EMAIL_FROM`

**Manual Trigger:**
You can trigger the workflow manually from the GitHub Actions tab.

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

## 📁 Project Structure

```
portfolio-sentiment-agent/
├── agents/              # Agent implementations
│   ├── base_agent.py
│   ├── portfolio_agent.py
│   ├── news_agent.py
│   ├── sentiment_agent.py
│   ├── summarization_agent.py
│   ├── risk_agent.py
│   ├── email_agent.py
│   └── orchestrator.py
├── services/            # External service integrations
│   ├── news_api.py
│   ├── finnhub_api.py
│   ├── llm_service.py
│   ├── email_service.py
│   ├── sentiment_aggregator.py
│   └── portfolio_manager.py
├── db/                  # Database models and connection
│   ├── models.py
│   ├── connection.py
│   └── schema.sql
├── config/              # Configuration
│   ├── settings.py
│   └── logging_config.py
├── scripts/             # Utility scripts
│   ├── seed_users.py
│   ├── run_pipeline.py
│   └── validate_sentiment.py
├── tests/               # Test suite
├── main.py              # Entry point
├── requirements.txt
└── README.md
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

## 📝 License

MIT License

## 🤝 Contributing

Contributions welcome! Please open an issue or submit a pull request.

## 📞 Support

For issues or questions, please open a GitHub issue.

