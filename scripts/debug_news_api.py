#!/usr/bin/env python3
"""Debug script to test NewsAPI and Finnhub and see what's actually being returned."""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings
import requests
from dateutil import parser as date_parser


def test_newsapi(ticker: str = "AAPL"):
    """Test NewsAPI with different queries."""
    print(f"\n{'='*70}")
    print(f"TESTING NEWSAPI FOR {ticker}")
    print(f"{'='*70}\n")
    
    if not settings.NEWSAPI_KEY:
        print("❌ NEWSAPI_KEY not set!")
        return
    
    base_url = "https://newsapi.org/v2"
    headers = {"X-Api-Key": settings.NEWSAPI_KEY}
    
    to_date = datetime.utcnow()
    from_date = to_date - timedelta(hours=24)
    
    # Test different queries
    queries = [
        # Current restrictive query
        f"({ticker}) AND (earnings OR stock OR market OR financial)",
        # Just ticker
        ticker,
        # Company name
        "Apple" if ticker == "AAPL" else "Microsoft" if ticker == "MSFT" else "Google",
        # Ticker OR company name
        f"{ticker} OR Apple" if ticker == "AAPL" else f"{ticker} OR Microsoft",
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n📊 Query #{i}: '{query}'")
        print("-" * 70)
        
        params = {
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 5,
            "from": from_date.isoformat(),
            "to": to_date.isoformat(),
        }
        
        try:
            response = requests.get(f"{base_url}/everything", params=params, headers=headers, timeout=10)
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 429:
                print("❌ RATE LIMITED - You've exceeded 100 requests/day")
                print("   Wait 24 hours or upgrade to paid tier")
                return
            
            if response.status_code == 401:
                print("❌ UNAUTHORIZED - Check your NEWSAPI_KEY")
                return
            
            response.raise_for_status()
            data = response.json()
            
            total_results = data.get("totalResults", 0)
            articles = data.get("articles", [])
            
            print(f"Total results: {total_results}")
            print(f"Articles returned: {len(articles)}")
            
            if articles:
                print(f"\n✅ Sample article:")
                article = articles[0]
                print(f"   Title: {article.get('title', 'N/A')[:80]}...")
                print(f"   Source: {article.get('source', {}).get('name', 'N/A')}")
                print(f"   Published: {article.get('publishedAt', 'N/A')}")
                print(f"   Content length: {len(article.get('content', '') or article.get('description', '') or '')}")
                print(f"   URL: {article.get('url', 'N/A')}")
            else:
                print("   ⚠️  No articles found")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error: {e}")


def test_finnhub(ticker: str = "AAPL"):
    """Test Finnhub API."""
    print(f"\n{'='*70}")
    print(f"TESTING FINNHUB FOR {ticker}")
    print(f"{'='*70}\n")
    
    if not settings.FINNHUB_KEY:
        print("❌ FINNHUB_KEY not set!")
        return
    
    base_url = "https://finnhub.io/api/v1"
    
    to_timestamp = int(datetime.utcnow().timestamp())
    from_timestamp = int((datetime.utcnow() - timedelta(hours=24)).timestamp())
    
    params = {
        "symbol": ticker,
        "token": settings.FINNHUB_KEY,
        "from": from_timestamp,
        "to": to_timestamp,
    }
    
    try:
        response = requests.get(f"{base_url}/company-news", params=params, timeout=10)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 429:
            print("❌ RATE LIMITED - You've exceeded 60 requests/minute")
            return
        
        if response.status_code == 401:
            print("❌ UNAUTHORIZED - Check your FINNHUB_KEY")
            return
        
        if response.status_code == 422:
            print("❌ UNPROCESSABLE ENTITY - Invalid ticker or date range")
            print("   Common on weekends/holidays for some tickers")
            return
        
        response.raise_for_status()
        articles = response.json()
        
        if not isinstance(articles, list):
            print(f"❌ Unexpected response: {articles}")
            return
        
        print(f"Articles returned: {len(articles)}")
        
        if articles:
            print(f"\n✅ Sample article:")
            article = articles[0]
            print(f"   Headline: {article.get('headline', 'N/A')[:80]}...")
            print(f"   Source: {article.get('source', 'N/A')}")
            print(f"   Published: {datetime.fromtimestamp(article.get('datetime', 0))}")
            print(f"   Content length: {len(article.get('summary', ''))}")
            print(f"   URL: {article.get('url', 'N/A')}")
        else:
            print("   ⚠️  No articles found")
            print("   Try a different ticker or time range")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")


def check_api_keys():
    """Check if API keys are configured."""
    print(f"\n{'='*70}")
    print("CHECKING API CONFIGURATION")
    print(f"{'='*70}\n")
    
    keys = {
        "NEWSAPI_KEY": settings.NEWSAPI_KEY,
        "FINNHUB_KEY": settings.FINNHUB_KEY,
    }
    
    for name, value in keys.items():
        if value:
            print(f"✅ {name}: {value[:10]}...{value[-4:]}")
        else:
            print(f"❌ {name}: NOT SET")
    
    print(f"\nSettings:")
    print(f"  NEWS_TIME_WINDOW_HOURS: {settings.NEWS_TIME_WINDOW_HOURS}")
    print(f"  NEWS_MIN_ARTICLE_LENGTH: {settings.NEWS_MIN_ARTICLE_LENGTH}")
    print(f"  NEWS_MAX_ARTICLES_PER_TICKER: {settings.NEWS_MAX_ARTICLES_PER_TICKER}")


def main():
    """Run debug tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Debug news API fetching")
    parser.add_argument("--ticker", default="AAPL", help="Ticker to test (default: AAPL)")
    args = parser.parse_args()
    
    print("\n🔍 NEWS API DEBUG TOOL")
    print(f"Testing ticker: {args.ticker}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Local)")
    print(f"Day of week: {datetime.now().strftime('%A')}")
    
    check_api_keys()
    test_newsapi(args.ticker)
    test_finnhub(args.ticker)
    
    print(f"\n{'='*70}")
    print("RECOMMENDATIONS")
    print(f"{'='*70}")
    print("""
1. If you're rate limited:
   - NewsAPI: Wait 24 hours (100 requests/day limit)
   - Finnhub: Wait 1 minute (60 requests/minute limit)

2. If no articles found:
   - Try running on weekdays (Mon-Fri) when markets are open
   - Use more popular stocks: AAPL, MSFT, GOOGL, TSLA, NVDA
   - Try different tickers

3. If content is too short:
   - Lower NEWS_MIN_ARTICLE_LENGTH in .env
   - Add: NEWS_MIN_ARTICLE_LENGTH=100

4. For better results:
   - Upgrade to NewsAPI paid tier ($449/mo for business endpoints)
   - Or use alternative APIs: Alpha Vantage, Polygon.io
    """)


if __name__ == "__main__":
    main()

