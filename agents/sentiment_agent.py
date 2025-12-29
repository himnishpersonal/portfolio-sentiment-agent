"""Sentiment Agent - analyzes financial sentiment using FinBERT."""

import logging
from typing import Any, Dict, List

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers import pipeline

from db import db_manager, Article as ArticleModel, SentimentScore as SentimentScoreModel
from agents.base_agent import BaseAgent
from agents.schemas import SentimentInput, SentimentOutput, ArticleData, SentimentResult
from config.settings import settings

logger = logging.getLogger(__name__)


class SentimentAgent(BaseAgent):
    """Agent for sentiment analysis using FinBERT."""

    def __init__(self):
        """Initialize Sentiment Agent."""
        super().__init__("SentimentAgent")
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._load_model()

    def _load_model(self) -> None:
        """Load FinBERT model and tokenizer."""
        try:
            self.logger.info(f"Loading FinBERT model on {self.device}")
            model_name = settings.SENTIMENT_MODEL

            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)

            # Move model to device
            self.model.to(self.device)
            self.model.eval()

            # Create pipeline for easier inference
            self.pipeline = pipeline(
                "sentiment-analysis",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device == "cuda" else -1,
                return_all_scores=True,
            )

            self.logger.info(f"FinBERT model loaded successfully on {self.device}")

        except Exception as e:
            self.logger.error(f"Failed to load FinBERT model: {e}")
            raise

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sentiment for articles.

        Args:
            input_data: Must contain 'articles' list.

        Returns:
            Dictionary with 'sentiments' list.
        """
        # Validate input
        sentiment_input = SentimentInput(**input_data)
        articles = sentiment_input.articles

        if not articles:
            self.logger.warning("No articles provided for sentiment analysis")
            return SentimentOutput(sentiments=[]).model_dump()

        self.logger.info(f"Analyzing sentiment for {len(articles)} articles")

        # Prepare texts for batch inference
        texts = []
        for article in articles:
            # Combine headline and content (truncate content to 500 chars)
            text = f"{article.headline} {article.content[:500]}"
            texts.append(text)

        # Batch inference
        sentiments = []
        batch_size = settings.SENTIMENT_BATCH_SIZE

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            batch_articles = articles[i : i + batch_size]

            try:
                # Run inference
                results = self.pipeline(batch_texts)

                for result, article in zip(results, batch_articles):
                    # Extract sentiment scores
                    # FinBERT returns: positive, negative, neutral
                    scores_dict = {item["label"].lower(): item["score"] for item in result}

                    # Get label with highest score
                    label = max(scores_dict, key=scores_dict.get)
                    confidence = scores_dict[label]

                    # Map to sentiment score with granularity based on confidence
                    if label == "positive":
                        # Use confidence to create range: 0.5 to 1.0
                        score = 0.5 + (confidence * 0.5)
                    elif label == "negative":
                        # Use confidence to create range: -0.5 to -1.0
                        score = -0.5 - (confidence * 0.5)
                    else:  # neutral
                        # Even neutrals can have slight bias based on positive/negative scores
                        positive_score = scores_dict.get("positive", 0.0)
                        negative_score = scores_dict.get("negative", 0.0)
                        if positive_score > negative_score + 0.1:
                            score = positive_score * 0.3  # Slight positive bias
                        elif negative_score > positive_score + 0.1:
                            score = -negative_score * 0.3  # Slight negative bias
                        else:
                            score = 0.0  # True neutral

                    # Store in database
                    article_id = self._get_article_id(article)
                    if article_id:
                        self._store_sentiment(article_id, label, confidence, score)

                    sentiments.append(
                        SentimentResult(
                            article_id=article_id,
                            label=label,
                            confidence=confidence,
                            score=score,
                        )
                    )

            except Exception as e:
                self.logger.error(f"Error in batch sentiment analysis: {e}")
                # Add neutral sentiment for failed articles
                for article in batch_articles:
                    article_id = self._get_article_id(article)
                    sentiments.append(
                        SentimentResult(article_id=article_id, label="neutral", confidence=0.5, score=0.0)
                    )

        self.logger.info(f"Completed sentiment analysis for {len(sentiments)} articles")

        # Return output
        output = SentimentOutput(sentiments=sentiments)
        return output.model_dump()

    def _get_article_id(self, article: ArticleData) -> int | None:
        """Get article ID from database by content hash.

        Args:
            article: Article data.

        Returns:
            Article ID or None if not found.
        """
        try:
            import hashlib

            content_hash = hashlib.sha256(f"{article.headline}{article.source}".encode()).hexdigest()

            with db_manager.get_session() as session:
                db_article = (
                    session.query(ArticleModel).filter(ArticleModel.content_hash == content_hash).first()
                )
                return db_article.id if db_article else None
        except Exception as e:
            self.logger.warning(f"Error getting article ID: {e}")
            return None

    def _store_sentiment(
        self, article_id: int, label: str, confidence: float, score: float
    ) -> None:
        """Store sentiment score in database.

        Args:
            article_id: Article ID.
            label: Sentiment label.
            confidence: Confidence score.
            score: Sentiment score.
        """
        try:
            with db_manager.get_session() as session:
                sentiment = SentimentScoreModel(
                    article_id=article_id,
                    label=label,
                    confidence=float(confidence),
                    score=float(score),
                    model_version=settings.SENTIMENT_MODEL,
                )
                session.add(sentiment)
                session.commit()
        except Exception as e:
            self.logger.warning(f"Error storing sentiment: {e}")

