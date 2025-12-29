"""Configuration management using Pydantic settings.

Supports multiple deployment environments:
- Local: .env file
- Google Cloud Composer: Secret Manager
- AWS/GitHub Actions: Environment variables
"""

import os
from typing import Literal

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

# Load environment variables from .env file (for local development)
load_dotenv()


def get_secret_from_gcp(secret_name: str) -> str | None:
    """Get secret from Google Cloud Secret Manager.
    
    Args:
        secret_name: Name of the secret.
        
    Returns:
        Secret value or None if not found.
    """
    try:
        from google.cloud import secretmanager
        
        project_id = os.environ.get("GCP_PROJECT_ID")
        if not project_id:
            return None
        
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except ImportError:
        # google-cloud-secret-manager not installed
        return None
    except Exception:
        # Secret not found or other error
        return None


def get_config_value(env_var: str, secret_name: str | None = None) -> str | None:
    """Get configuration value from environment or Secret Manager.
    
    Args:
        env_var: Environment variable name.
        secret_name: Optional Secret Manager secret name.
        
    Returns:
        Configuration value or None.
    """
    # First try environment variable
    value = os.environ.get(env_var)
    if value:
        return value
    
    # Then try Secret Manager (if in GCP)
    if secret_name and os.environ.get("GCP_PROJECT_ID"):
        return get_secret_from_gcp(secret_name)
    
    return None


class Settings(BaseSettings):
    """Application settings with validation."""

    # Database
    DATABASE_URL: str = Field(
        default_factory=lambda: get_config_value("DATABASE_URL", "database-url") or "",
        description="PostgreSQL database connection URL"
    )

    # API Keys
    NEWSAPI_KEY: str = Field(
        default_factory=lambda: get_config_value("NEWSAPI_KEY", "newsapi-key") or "",
        description="NewsAPI API key"
    )
    FINNHUB_KEY: str = Field(
        default_factory=lambda: get_config_value("FINNHUB_KEY", "finnhub-key") or "",
        description="Finnhub API key"
    )
    SENDGRID_API_KEY: str = Field(
        default_factory=lambda: get_config_value("SENDGRID_API_KEY", "sendgrid-key") or "",
        description="SendGrid API key"
    )

    # LLM Provider (anthropic, openai, or openrouter)
    LLM_PROVIDER: Literal["anthropic", "openai", "openrouter"] = Field(
        default="openrouter", description="LLM provider for summarization"
    )
    ANTHROPIC_API_KEY: str | None = Field(
        default_factory=lambda: get_config_value("ANTHROPIC_API_KEY", "anthropic-key"),
        description="Anthropic API key"
    )
    OPENAI_API_KEY: str | None = Field(
        default_factory=lambda: get_config_value("OPENAI_API_KEY", "openai-key"),
        description="OpenAI API key"
    )
    LLM_KEY: str | None = Field(
        default_factory=lambda: get_config_value("LLM_KEY", "llm-key"),
        description="OpenRouter API key (or generic LLM key)"
    )
    OPENROUTER_MODEL: str = Field(
        default="allenai/olmo-3.1-32b-think:free",
        description="OpenRouter model to use"
    )

    # Model Configuration
    SENTIMENT_MODEL: str = Field(
        default="ProsusAI/finbert", description="HuggingFace model for sentiment analysis"
    )
    SENTIMENT_BATCH_SIZE: int = Field(default=8, description="Batch size for sentiment inference")
    SENTIMENT_MAX_SEQUENCE_LENGTH: int = Field(
        default=512, description="Max sequence length for sentiment model"
    )

    # Email Configuration
    EMAIL_FROM: str = Field(
        default_factory=lambda: get_config_value("EMAIL_FROM", "email-from") or "",
        description="Sender email address"
    )
    EMAIL_FROM_NAME: str = Field(default="Portfolio Sentiment Agent", description="Sender name")

    # Risk Assessment Thresholds (more sensitive defaults)
    RISK_THRESHOLD_LOW: float = Field(default=0.10, description="Low risk threshold (adjusted for sentiment-weighted formula)")
    RISK_THRESHOLD_MEDIUM: float = Field(default=0.35, description="Medium risk threshold (adjusted for sentiment-weighted formula)")
    RISK_THRESHOLD_HIGH: float = Field(default=0.60, description="High risk threshold (adjusted for sentiment-weighted formula)")

    # News Configuration
    NEWS_TIME_WINDOW_HOURS: int = Field(default=24, description="Hours to look back for news")
    NEWS_MIN_ARTICLE_LENGTH: int = Field(default=300, description="Minimum article content length")
    NEWS_MAX_ARTICLES_PER_TICKER: int = Field(default=5, description="Max articles per ticker")

    # Source Credibility Weights
    SOURCE_WEIGHT_REUTERS: float = Field(default=1.0, description="Reuters credibility weight")
    SOURCE_WEIGHT_BLOOMBERG: float = Field(default=0.95, description="Bloomberg credibility weight")
    SOURCE_WEIGHT_CNBC: float = Field(default=0.85, description="CNBC credibility weight")
    SOURCE_WEIGHT_DEFAULT: float = Field(default=0.6, description="Default source credibility weight")

    # Recency Weights
    RECENCY_WEIGHT_6H: float = Field(default=1.0, description="Weight for articles 0-6 hours old")
    RECENCY_WEIGHT_12H: float = Field(default=0.8, description="Weight for articles 6-12 hours old")
    RECENCY_WEIGHT_24H: float = Field(default=0.6, description="Weight for articles 12-24 hours old")

    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: Literal["json", "text"] = Field(
        default="json", description="Log format (json for production, text for dev)"
    )

    class Config:
        """Pydantic config."""

        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()

