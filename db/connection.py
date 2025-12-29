"""Database connection manager with connection pooling and retry logic."""

import logging
import time
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from config.settings import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections with pooling and retry logic."""

    def __init__(self, database_url: str | None = None):
        """Initialize database manager.

        Args:
            database_url: Database connection URL. If None, uses settings.DATABASE_URL.
        """
        self.database_url = database_url or settings.DATABASE_URL
        self.engine: Engine | None = None
        self.SessionLocal: sessionmaker | None = None
        self._initialize_engine()

    def _initialize_engine(self) -> None:
        """Initialize SQLAlchemy engine with connection pooling."""
        try:
            self.engine = create_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,  # Verify connections before using
                pool_recycle=3600,  # Recycle connections after 1 hour
                echo=False,  # Set to True for SQL query logging
            )
            self.SessionLocal = sessionmaker(
                autocommit=False, autoflush=False, bind=self.engine
            )
            logger.info("Database engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database engine: {e}")
            raise

    @contextmanager
    def get_session(self, retries: int = 3, delay: float = 1.0) -> Generator[Session, None, None]:
        """Get database session with retry logic.

        Args:
            retries: Number of retry attempts on connection failure.
            delay: Delay between retries in seconds.

        Yields:
            Database session.

        Raises:
            Exception: If all retry attempts fail.
        """
        session = None
        last_exception = None

        for attempt in range(retries):
            try:
                if self.SessionLocal is None:
                    self._initialize_engine()
                session = self.SessionLocal()
                yield session
                session.commit()
                return
            except Exception as e:
                if session:
                    session.rollback()
                last_exception = e
                logger.warning(
                    f"Database connection attempt {attempt + 1}/{retries} failed: {e}"
                )
                if attempt < retries - 1:
                    time.sleep(delay * (attempt + 1))  # Exponential backoff
                else:
                    logger.error(f"All database connection attempts failed: {e}")
            finally:
                if session:
                    session.close()

        if last_exception:
            raise last_exception

    def test_connection(self) -> bool:
        """Test database connection.

        Returns:
            True if connection successful, False otherwise.
        """
        try:
            with self.get_session() as session:
                session.execute("SELECT 1")
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False


# Global database manager instance
db_manager = DatabaseManager()

