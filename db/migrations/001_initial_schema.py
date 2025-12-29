"""Initial database schema migration."""

from pathlib import Path
from sqlalchemy import text

# This is a placeholder migration file
# In production, use Alembic or similar migration tool

MIGRATION_SQL = Path(__file__).parent.parent / "schema.sql"


def upgrade(connection):
    """Apply migration."""
    with open(MIGRATION_SQL, "r") as f:
        sql = f.read()
        connection.execute(text(sql))
        connection.commit()


def downgrade(connection):
    """Rollback migration."""
    # Drop all tables
    tables = [
        "pipeline_runs",
        "email_log",
        "portfolio_sentiment",
        "sentiment_scores",
        "articles",
        "portfolio",
        "users",
    ]
    for table in tables:
        connection.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
    connection.commit()

