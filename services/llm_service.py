"""LLM service abstraction for text summarization."""

import logging
from abc import ABC, abstractmethod
from typing import List

from config.settings import settings
from services.news_api import Article

logger = logging.getLogger(__name__)


class Sentiment:
    """Sentiment data model."""

    def __init__(self, label: str, confidence: float, score: float):
        """Initialize sentiment.

        Args:
            label: Sentiment label (positive, neutral, negative).
            confidence: Confidence score (0.0 to 1.0).
            score: Sentiment score (-1.0 to 1.0).
        """
        self.label = label
        self.confidence = confidence
        self.score = score


class LLMService(ABC):
    """Abstract base class for LLM services."""

    @abstractmethod
    def summarize(
        self, ticker: str, articles: List[Article], sentiments: List[Sentiment]
    ) -> str:
        """Generate summary for ticker based on articles and sentiments.

        Args:
            ticker: Stock ticker symbol.
            articles: List of articles.
            sentiments: List of sentiment scores corresponding to articles.

        Returns:
            Summary text (2-3 sentences).
        """
        pass


class AnthropicService(LLMService):
    """Anthropic Claude service for summarization."""

    def __init__(self, api_key: str | None = None, model: str = "claude-3-haiku-20240307"):
        """Initialize Anthropic service.

        Args:
            api_key: Anthropic API key. If None, uses settings.ANTHROPIC_API_KEY.
            model: Model name to use.
        """
        try:
            from anthropic import Anthropic

            self.api_key = api_key or settings.ANTHROPIC_API_KEY
            if not self.api_key:
                raise ValueError("ANTHROPIC_API_KEY not set")
            self.client = Anthropic(api_key=self.api_key)
            self.model = model
        except ImportError:
            raise ImportError("anthropic package not installed. Install with: pip install anthropic")

    def summarize(
        self, ticker: str, articles: List[Article], sentiments: List[Sentiment]
    ) -> str:
        """Generate summary using Anthropic Claude."""
        try:
            # Build prompt
            sentiment_summary = self._build_sentiment_summary(articles, sentiments)
            articles_text = self._format_articles(articles)

            prompt = f"""Analyze the following financial news articles about {ticker} and provide a concise 2-3 sentence summary.

Focus on:
1. The cause (what happened) and its impact on the company
2. Explicitly mention the company name ({ticker})
3. The overall sentiment trend (improving/declining/stable)
4. Avoid hype language, be factual

Sentiment Analysis Summary:
{sentiment_summary}

Articles:
{articles_text}

Provide a clear, actionable financial summary:"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}],
            )

            summary = response.content[0].text.strip()
            logger.info(f"Generated summary for {ticker} using Anthropic")
            return summary

        except Exception as e:
            logger.error(f"Anthropic summarization failed for {ticker}: {e}")
            return f"{ticker}: Unable to generate summary due to API error."

    def _build_sentiment_summary(self, articles: List[Article], sentiments: List[Sentiment]) -> str:
        """Build sentiment summary text."""
        if not sentiments:
            return "No sentiment data available."

        positive_count = sum(1 for s in sentiments if s.label == "positive")
        negative_count = sum(1 for s in sentiments if s.label == "negative")
        neutral_count = sum(1 for s in sentiments if s.label == "neutral")
        avg_confidence = sum(s.confidence for s in sentiments) / len(sentiments)

        return f"Positive: {positive_count}, Neutral: {neutral_count}, Negative: {negative_count}. Average confidence: {avg_confidence:.2f}"

    def _format_articles(self, articles: List[Article]) -> str:
        """Format articles for prompt."""
        formatted = []
        for i, article in enumerate(articles[:5], 1):  # Limit to 5 articles
            formatted.append(
                f"{i}. {article.headline}\n   Source: {article.source}\n   {article.content[:300]}..."
            )
        return "\n\n".join(formatted)


class OpenAIService(LLMService):
    """OpenAI GPT service for summarization."""

    def __init__(self, api_key: str | None = None, model: str = "gpt-4-turbo-preview"):
        """Initialize OpenAI service.

        Args:
            api_key: OpenAI API key. If None, uses settings.OPENAI_API_KEY.
            model: Model name to use.
        """
        try:
            from openai import OpenAI

            self.api_key = api_key or settings.OPENAI_API_KEY
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY not set")
            self.client = OpenAI(api_key=self.api_key)
            self.model = model
        except ImportError:
            raise ImportError("openai package not installed. Install with: pip install openai")

    def summarize(
        self, ticker: str, articles: List[Article], sentiments: List[Sentiment]
    ) -> str:
        """Generate summary using OpenAI GPT."""
        try:
            # Build prompt (same as Anthropic)
            sentiment_summary = self._build_sentiment_summary(articles, sentiments)
            articles_text = self._format_articles(articles)

            prompt = f"""Analyze the following financial news articles about {ticker} and provide a concise 2-3 sentence summary.

Focus on:
1. The cause (what happened) and its impact on the company
2. Explicitly mention the company name ({ticker})
3. The overall sentiment trend (improving/declining/stable)
4. Avoid hype language, be factual

Sentiment Analysis Summary:
{sentiment_summary}

Articles:
{articles_text}

Provide a clear, actionable financial summary:"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.3,
            )

            summary = response.choices[0].message.content.strip()
            logger.info(f"Generated summary for {ticker} using OpenAI")
            return summary

        except Exception as e:
            logger.error(f"OpenAI summarization failed for {ticker}: {e}")
            return f"{ticker}: Unable to generate summary due to API error."

    def _build_sentiment_summary(self, articles: List[Article], sentiments: List[Sentiment]) -> str:
        """Build sentiment summary text."""
        if not sentiments:
            return "No sentiment data available."

        positive_count = sum(1 for s in sentiments if s.label == "positive")
        negative_count = sum(1 for s in sentiments if s.label == "negative")
        neutral_count = sum(1 for s in sentiments if s.label == "neutral")
        avg_confidence = sum(s.confidence for s in sentiments) / len(sentiments)

        return f"Positive: {positive_count}, Neutral: {neutral_count}, Negative: {negative_count}. Average confidence: {avg_confidence:.2f}"

    def _format_articles(self, articles: List[Article]) -> str:
        """Format articles for prompt."""
        formatted = []
        for i, article in enumerate(articles[:5], 1):  # Limit to 5 articles
            formatted.append(
                f"{i}. {article.headline}\n   Source: {article.source}\n   {article.content[:300]}..."
            )
        return "\n\n".join(formatted)


class OpenRouterService(LLMService):
    """OpenRouter service for summarization (supports free models)."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "allenai/olmo-3.1-32b-think:free"
    ):
        """Initialize OpenRouter service.

        Args:
            api_key: OpenRouter API key. If None, uses settings.LLM_KEY.
            model: Model name to use.
        """
        self.api_key = api_key or settings.LLM_KEY
        if not self.api_key:
            raise ValueError("LLM_KEY not set for OpenRouter")
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1"

    def summarize(
        self, ticker: str, articles: List[Article], sentiments: List[Sentiment]
    ) -> str:
        """Generate summary using OpenRouter."""
        try:
            import requests

            # Build simplified prompt for weaker models
            sentiment_summary = self._build_sentiment_summary(articles, sentiments)
            articles_text = self._format_articles(articles)

            prompt = f"""Analyze these 3 news articles for {ticker}. Write a concise 2-3 sentence summary.

Guidelines:
- If articles discuss {ticker} directly: summarize the key company news (earnings, products, deals, outlook)
- If articles discuss the broader market/sector: explain the market context and potential impact on {ticker}
- Be professional and direct - no preambles or meta-commentary
- Focus on what {ticker} investors need to know

Articles:
{articles_text}

Sentiment: {sentiment_summary}

Write the summary (2-3 sentences, no preamble):"""

            # OpenRouter uses OpenAI-compatible format
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a financial analyst. Write concise, factual summaries without explaining your thinking process. Just provide the final summary."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": 200,
                    "temperature": 0.4,
                    "stop": ["\n\n\n", "---", "Note:", "Summary:", "Article", "IMPORTANT:"]
                },
                timeout=30,
            )
            response.raise_for_status()
            
            result = response.json()
            message = result["choices"][0]["message"]
            
            # The "think" models put responses in "reasoning" field
            # Regular models use "content" field
            summary = message.get("content") or message.get("reasoning") or ""
            
            if summary:
                summary = summary.strip()
            
            if not summary:
                logger.warning(f"Empty response from OpenRouter for {ticker}")
                return f"{ticker}: Unable to generate summary due to empty API response."
            
            # Clean up instruction markers and formatting artifacts
            summary = self._clean_response(summary)
            
            logger.info(f"Generated summary for {ticker} using OpenRouter ({self.model})")
            return summary

        except Exception as e:
            logger.error(f"OpenRouter summarization failed for {ticker}: {e}")
            return f"{ticker}: Unable to generate summary due to API error."

    def _build_sentiment_summary(self, articles: List[Article], sentiments: List[Sentiment]) -> str:
        """Build sentiment summary text."""
        if not sentiments:
            return "No sentiment data available."

        positive_count = sum(1 for s in sentiments if s.label == "positive")
        negative_count = sum(1 for s in sentiments if s.label == "negative")
        neutral_count = sum(1 for s in sentiments if s.label == "neutral")
        avg_confidence = sum(s.confidence for s in sentiments) / len(sentiments)

        return f"Positive: {positive_count}, Neutral: {neutral_count}, Negative: {negative_count}. Average confidence: {avg_confidence:.2f}"

    def _format_articles(self, articles: List[Article]) -> str:
        """Format articles for prompt."""
        if not articles:
            return "No articles available."
        
        formatted = []
        for i, article in enumerate(articles[:5], 1):  # Limit to 5 articles
            # Show more content for better context
            content_preview = article.content[:500] if article.content else article.headline
            formatted.append(
                f"Article {i}:\n"
                f"Headline: {article.headline}\n"
                f"Source: {article.source}\n"
                f"Content: {content_preview}...\n"
                f"URL: {article.url}"
            )
        return "\n\n".join(formatted)
    
    def _clean_response(self, text: str) -> str:
        """Clean instruction markers and formatting artifacts from response.
        
        Args:
            text: Raw response text
            
        Returns:
            Cleaned text
        """
        import re
        
        # Remove instruction markers (Mistral, Llama, etc.)
        text = re.sub(r'\[/?(?:B_)?INST\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\[/?(?:B_)?/INST\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\[/?SYS\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'<\|.*?\|>', '', text)  # Remove special tokens
        
        # Remove informal preambles and meta-commentary
        text = re.sub(r'^Here is (a|an|the) .*?summary.*?:\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^Here\'s (a|an|the) .*?summary.*?:\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^(Summary|Analysis):\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^Based on .*?, ', '', text, flags=re.IGNORECASE)
        
        # Remove excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = text.strip()
        
        return text


def get_llm_service() -> LLMService:
    """Get LLM service based on configuration.

    Returns:
        LLMService instance.
    """
    provider = settings.LLM_PROVIDER

    if provider == "anthropic":
        return AnthropicService()
    elif provider == "openai":
        return OpenAIService()
    elif provider == "openrouter":
        return OpenRouterService(model=settings.OPENROUTER_MODEL)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")

