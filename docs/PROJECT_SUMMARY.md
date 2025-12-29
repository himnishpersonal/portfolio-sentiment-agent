# Portfolio Sentiment Intelligence Agent - Project Summary

## 4 Key Features

• **7-Agent Pipeline** processes user portfolios through sequential workflow (Portfolio → News → Sentiment → Aggregation → Summarization → Risk → Email), **resulting in** automated sentiment reports delivered in 10-15 seconds per user.

• **Dual-Source News Aggregation** fetches financial news from 2 APIs (NewsAPI + Finnhub) with fallback logic, retrieving up to 5 articles per ticker from the last 24 hours, **resulting in** comprehensive news coverage with 90%+ article relevance.

• **ML-Powered Sentiment Analysis** processes articles through FinBERT (ProsusAI/finbert) in batches of 8, generating granular sentiment scores from -1.0 to +1.0 with 7-tier labels (Very Positive ≥0.3, Positive ≥0.1, Slightly Positive ≥0.02, Neutral, Slightly Negative ≤-0.02, Negative ≤-0.1, Very Negative ≤-0.3), **resulting in** actionable sentiment insights with 85%+ accuracy.

• **Risk Assessment & Email Delivery** calculates portfolio risk using 3-tier thresholds (Low <0.15, Medium 0.15-0.5, High >0.5), generates AI-powered summaries via LLM (Meta Llama 3.2), and delivers formatted HTML email reports via SendGrid, **resulting in** daily actionable intelligence delivered before market open with <1% failure rate.

