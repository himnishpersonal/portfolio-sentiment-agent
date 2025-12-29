"""Orchestrator Agent - coordinates full pipeline execution using LangGraph."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, TypedDict

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from db import db_manager, User, PipelineRun
from agents.portfolio_agent import PortfolioAgent
from agents.news_agent import NewsAgent
from agents.sentiment_agent import SentimentAgent
from agents.summarization_agent import SummarizationAgent
from agents.risk_agent import RiskAgent
from agents.email_agent import EmailAgent
from services.sentiment_aggregator import aggregate_ticker_sentiment
from agents.schemas import ArticleData, SentimentResult

logger = logging.getLogger(__name__)


class PipelineState(TypedDict):
    """State schema for LangGraph pipeline."""

    user_id: int
    user_email: str
    portfolio: Dict[str, float]
    articles_by_ticker: Dict[str, list[ArticleData]]
    sentiments_by_article: Dict[str, list[SentimentResult]]
    ticker_sentiments: Dict[str, float]
    ticker_confidences: Dict[str, float]
    summaries_by_ticker: Dict[str, str]
    risk_assessment: Dict[str, Any]
    email_sent: bool
    error: str | None
    pipeline_run_id: int | None


class Orchestrator:
    """Orchestrator for multi-agent pipeline using LangGraph."""

    def __init__(self):
        """Initialize orchestrator."""
        self.logger = logging.getLogger(__name__)
        self.portfolio_agent = PortfolioAgent()
        self.news_agent = NewsAgent()
        self.sentiment_agent = SentimentAgent()
        self.summarization_agent = SummarizationAgent()
        self.risk_agent = RiskAgent()
        self.email_agent = EmailAgent()

        # Build LangGraph workflow
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build LangGraph workflow.

        Returns:
            Compiled StateGraph.
        """
        workflow = StateGraph(PipelineState)

        # Add nodes
        workflow.add_node("portfolio", self._portfolio_node)
        workflow.add_node("news", self._news_node)
        workflow.add_node("sentiment", self._sentiment_node)
        workflow.add_node("aggregate", self._aggregate_node)
        workflow.add_node("summarization", self._summarization_node)
        workflow.add_node("risk", self._risk_node)
        workflow.add_node("email", self._email_node)

        # Define edges
        workflow.set_entry_point("portfolio")
        workflow.add_edge("portfolio", "news")
        workflow.add_edge("news", "sentiment")
        workflow.add_edge("sentiment", "aggregate")
        workflow.add_edge("aggregate", "summarization")
        workflow.add_edge("summarization", "risk")
        workflow.add_edge("risk", "email")
        workflow.add_edge("email", END)

        # Compile without checkpointing (simpler for local runs)
        return workflow.compile()

    def run(self, user_id: int) -> Dict[str, Any]:
        """Run pipeline for a user.

        Args:
            user_id: User ID.

        Returns:
            Final pipeline state.
        """
        # Get user email
        with db_manager.get_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            user_email = user.email

        # Create pipeline run record
        pipeline_run_id = self._create_pipeline_run(user_id)

        # Initialize state
        initial_state: PipelineState = {
            "user_id": user_id,
            "user_email": user_email,
            "portfolio": {},
            "articles_by_ticker": {},
            "sentiments_by_article": {},
            "ticker_sentiments": {},
            "ticker_confidences": {},
            "summaries_by_ticker": {},
            "risk_assessment": {},
            "email_sent": False,
            "error": None,
            "pipeline_run_id": pipeline_run_id,
        }

        try:
            self.logger.info(f"Starting pipeline for user {user_id}")

            # Run graph and collect final state
            final_state = initial_state.copy()
            for step_output in self.graph.stream(initial_state):
                # LangGraph returns dict with node names as keys
                for node_name, node_state in step_output.items():
                    final_state.update(node_state)
                    # Log progress
                    if node_name == "portfolio":
                        self.logger.info("Portfolio agent completed")
                    elif node_name == "news":
                        self.logger.info("News agent completed")
                    elif node_name == "sentiment":
                        self.logger.info("Sentiment agent completed")
                    elif node_name == "aggregate":
                        self.logger.info("Aggregation completed")
                    elif node_name == "summarization":
                        self.logger.info("Summarization agent completed")
                    elif node_name == "risk":
                        self.logger.info("Risk agent completed")
                    elif node_name == "email":
                        self.logger.info("Email agent completed")

            # Update pipeline run
            self._update_pipeline_run(pipeline_run_id, "completed", None)

            self.logger.info(f"Pipeline completed successfully for user {user_id}")
            return final_state

        except Exception as e:
            self.logger.error(f"Pipeline failed for user {user_id}: {e}", exc_info=True)
            self._update_pipeline_run(pipeline_run_id, "failed", str(e))
            raise

    def _portfolio_node(self, state: PipelineState) -> PipelineState:
        """Portfolio agent node."""
        try:
            output = self.portfolio_agent.run({"user_id": state["user_id"]})
            state["portfolio"] = output["portfolio"]
            return state
        except Exception as e:
            state["error"] = f"Portfolio agent failed: {e}"
            raise

    def _news_node(self, state: PipelineState) -> PipelineState:
        """News agent node."""
        try:
            tickers = list(state["portfolio"].keys())
            output = self.news_agent.run({"tickers": tickers})
            state["articles_by_ticker"] = {
                ticker: [
                    ArticleData(**article) if isinstance(article, dict) else article
                    for article in articles
                ]
                for ticker, articles in output["articles_by_ticker"].items()
            }
            return state
        except Exception as e:
            state["error"] = f"News agent failed: {e}"
            raise

    def _sentiment_node(self, state: PipelineState) -> PipelineState:
        """Sentiment agent node."""
        try:
            all_articles = []
            for articles in state["articles_by_ticker"].values():
                all_articles.extend(articles)

            if not all_articles:
                state["sentiments_by_article"] = {}
                return state

            output = self.sentiment_agent.run({"articles": [a.model_dump() if hasattr(a, "model_dump") else a for a in all_articles]})
            state["sentiments_by_article"] = {
                "all": [
                    SentimentResult(**s) if isinstance(s, dict) else s
                    for s in output["sentiments"]
                ]
            }
            return state
        except Exception as e:
            state["error"] = f"Sentiment agent failed: {e}"
            raise

    def _aggregate_node(self, state: PipelineState) -> PipelineState:
        """Aggregate sentiments by ticker."""
        try:
            all_sentiments = state["sentiments_by_article"].get("all", [])
            sentiment_index = 0

            ticker_sentiments: Dict[str, float] = {}
            ticker_confidences: Dict[str, float] = {}

            for ticker, articles in state["articles_by_ticker"].items():
                if not articles:
                    ticker_sentiments[ticker] = 0.0
                    ticker_confidences[ticker] = 0.0
                    continue

                # Get sentiments for this ticker's articles
                ticker_sentiment_list = all_sentiments[sentiment_index : sentiment_index + len(articles)]
                sentiment_index += len(articles)

                # Convert ArticleData to Article objects for aggregation
                from services.news_api import Article
                article_objects = []
                for a in articles:
                    published_at = a.published_at if hasattr(a, "published_at") else a.get("published_at")
                    # Ensure timezone-aware datetime
                    if published_at and published_at.tzinfo is None:
                        published_at = published_at.replace(tzinfo=timezone.utc)
                    
                    article_objects.append(Article(
                        headline=a.headline if hasattr(a, "headline") else a.get("headline", ""),
                        content=a.content if hasattr(a, "content") else a.get("content", ""),
                        source=a.source if hasattr(a, "source") else a.get("source", ""),
                        url=a.url if hasattr(a, "url") else a.get("url", ""),
                        published_at=published_at,
                        ticker=a.ticker if hasattr(a, "ticker") else a.get("ticker", ""),
                    ))

                # Convert SentimentResult to Sentiment objects
                from services.llm_service import Sentiment
                sentiment_objects = [
                    Sentiment(
                        label=s.label if hasattr(s, "label") else s.get("label", "neutral"),
                        confidence=s.confidence if hasattr(s, "confidence") else s.get("confidence", 0.5),
                        score=s.score if hasattr(s, "score") else s.get("score", 0.0),
                    )
                    for s in ticker_sentiment_list
                ]

                # Aggregate
                sentiment_score, avg_confidence = aggregate_ticker_sentiment(
                    article_objects, sentiment_objects
                )

                ticker_sentiments[ticker] = sentiment_score
                ticker_confidences[ticker] = avg_confidence

            state["ticker_sentiments"] = ticker_sentiments
            state["ticker_confidences"] = ticker_confidences
            return state
        except Exception as e:
            state["error"] = f"Aggregation failed: {e}"
            raise

    def _summarization_node(self, state: PipelineState) -> PipelineState:
        """Summarization agent node."""
        try:
            # Prepare ticker data
            ticker_data = {}
            all_sentiments = state["sentiments_by_article"].get("all", [])
            sentiment_index = 0

            self.logger.info(f"Summarization node - articles_by_ticker keys: {list(state['articles_by_ticker'].keys())}")
            
            for ticker, articles in state["articles_by_ticker"].items():
                self.logger.info(f"Summarization node - {ticker}: {len(articles)} articles")
                ticker_sentiment_list = all_sentiments[sentiment_index : sentiment_index + len(articles)]
                sentiment_index += len(articles)

                ticker_data[ticker] = {
                    "articles": [a.model_dump() if hasattr(a, "model_dump") else a for a in articles],
                    "sentiments": [s.model_dump() if hasattr(s, "model_dump") else s for s in ticker_sentiment_list],
                }
                self.logger.info(f"Prepared ticker_data[{ticker}]: {len(ticker_data[ticker]['articles'])} articles, {len(ticker_data[ticker]['sentiments'])} sentiments")

            output = self.summarization_agent.run({"ticker_data": ticker_data})
            state["summaries_by_ticker"] = output.get("summaries_by_ticker", {})
            return state
        except Exception as e:
            state["error"] = f"Summarization agent failed: {e}"
            raise

    def _risk_node(self, state: PipelineState) -> PipelineState:
        """Risk agent node."""
        try:
            # Prepare ticker articles for risk assessment
            ticker_articles = {
                ticker: [a.model_dump() if hasattr(a, "model_dump") else a for a in articles]
                for ticker, articles in state["articles_by_ticker"].items()
            }

            output = self.risk_agent.run(
                {
                    "portfolio": state["portfolio"],
                    "ticker_sentiments": state["ticker_sentiments"],
                    "ticker_confidences": state["ticker_confidences"],
                    "ticker_articles": ticker_articles,
                    "user_id": state["user_id"],
                }
            )
            state["risk_assessment"] = output
            return state
        except Exception as e:
            state["error"] = f"Risk agent failed: {e}"
            raise

    def _email_node(self, state: PipelineState) -> PipelineState:
        """Email agent node."""
        try:
            # Prepare ticker data for email
            ticker_data = {}
            for ticker in state["portfolio"].keys():
                articles = state["articles_by_ticker"].get(ticker, [])
                ticker_data[ticker] = {
                    "sentiment": state["ticker_sentiments"].get(ticker, 0.0),
                    "summary": state["summaries_by_ticker"].get(ticker, "No summary available"),
                    "risk_level": state["risk_assessment"].get("ticker_risks", {}).get(ticker, "medium"),
                    "articles": [
                        {
                            "headline": a.headline if hasattr(a, "headline") else a.get("headline", ""),
                            "url": a.url if hasattr(a, "url") else a.get("url", ""),
                        }
                        for a in articles[:3]  # Limit to 3 articles
                    ],
                }

            output = self.email_agent.run(
                {
                    "user_email": state["user_email"],
                    "portfolio": state["portfolio"],
                    "ticker_data": ticker_data,
                    "portfolio_risk": state["risk_assessment"].get("risk_level", "medium"),
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "user_id": state["user_id"],
                }
            )
            state["email_sent"] = output.get("success", False)
            return state
        except Exception as e:
            state["error"] = f"Email agent failed: {e}"
            raise

    def _create_pipeline_run(self, user_id: int) -> int:
        """Create pipeline run record.

        Args:
            user_id: User ID.

        Returns:
            Pipeline run ID.
        """
        try:
            with db_manager.get_session() as session:
                pipeline_run = PipelineRun(
                    user_id=user_id,
                    status="running",
                    started_at=datetime.now(timezone.utc),
                )
                session.add(pipeline_run)
                session.commit()
                session.refresh(pipeline_run)
                return pipeline_run.id
        except Exception as e:
            self.logger.warning(f"Error creating pipeline run: {e}")
            return 0

    def _update_pipeline_run(self, pipeline_run_id: int, status: str, error_message: str | None) -> None:
        """Update pipeline run record.

        Args:
            pipeline_run_id: Pipeline run ID.
            status: Final status.
            error_message: Error message if failed.
        """
        try:
            if pipeline_run_id == 0:
                return

            with db_manager.get_session() as session:
                pipeline_run = session.query(PipelineRun).filter(PipelineRun.id == pipeline_run_id).first()
                if pipeline_run:
                    pipeline_run.status = status
                    pipeline_run.completed_at = datetime.now(timezone.utc)
                    pipeline_run.error_message = error_message
                    if pipeline_run.started_at:
                        execution_time = (pipeline_run.completed_at - pipeline_run.started_at).total_seconds()
                        pipeline_run.execution_time_seconds = int(execution_time)
                    session.commit()
        except Exception as e:
            self.logger.warning(f"Error updating pipeline run: {e}")

