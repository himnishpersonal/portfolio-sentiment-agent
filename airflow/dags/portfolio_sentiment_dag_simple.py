"""
Simplified Airflow DAG for Portfolio Sentiment Intelligence Agent.

This version processes all users sequentially in a single task.
Best for small deployments or when ML model memory is a concern.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago

# Import pipeline components
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.orchestrator import Orchestrator
from db import db_manager, User
from config.logging_config import setup_logging

# Setup logging
setup_logging()

# Default arguments for DAG
default_args = {
    'owner': 'portfolio-sentiment-team',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'start_date': days_ago(1),
}

# Create DAG
dag = DAG(
    'portfolio_sentiment_daily_simple',
    default_args=default_args,
    description='Daily portfolio sentiment analysis (simplified)',
    schedule_interval='0 13 * * 1-5',  # 8am EST (1pm UTC) on weekdays
    catchup=False,
    tags=['portfolio', 'sentiment', 'ml'],
    max_active_runs=1,
)


def run_complete_pipeline(**context):
    """Run the complete sentiment pipeline for all users.
    
    This is a simplified version that processes all users in sequence
    within a single Airflow task.
    """
    try:
        # Verify database connection
        if not db_manager.test_connection():
            raise Exception("Database connection failed")
        print("✓ Database connection verified")
        
        # Get all users
        with db_manager.get_session() as session:
            users = session.query(User).all()
        
        if not users:
            print("No users found in database")
            return {"total": 0, "success": 0, "failed": 0}
        
        print(f"Found {len(users)} users to process")
        
        # Initialize orchestrator
        orchestrator = Orchestrator()
        
        # Process each user
        results = []
        success_count = 0
        failure_count = 0
        
        for user in users:
            try:
                print(f"\n{'='*60}")
                print(f"Processing user {user.id} ({user.email})...")
                print(f"{'='*60}")
                
                result = orchestrator.run(user.id)
                
                if result.get("email_sent"):
                    print(f"✓ Successfully processed user {user.id}")
                    results.append({
                        "user_id": user.id,
                        "user_email": user.email,
                        "status": "success"
                    })
                    success_count += 1
                else:
                    print(f"⚠ User {user.id} processed but email may not have been sent")
                    results.append({
                        "user_id": user.id,
                        "user_email": user.email,
                        "status": "warning"
                    })
                    success_count += 1  # Still count as success
                    
            except Exception as e:
                print(f"✗ Failed to process user {user.id}: {e}")
                results.append({
                    "user_id": user.id,
                    "user_email": user.email,
                    "status": "failed",
                    "error": str(e)
                })
                failure_count += 1
        
        # Print summary
        print(f"\n{'='*60}")
        print("Pipeline Execution Summary")
        print(f"{'='*60}")
        print(f"Total Users: {len(users)}")
        print(f"Successful: {success_count}")
        print(f"Failed: {failure_count}")
        print(f"{'='*60}\n")
        
        return {
            "total": len(users),
            "success": success_count,
            "failed": failure_count,
            "results": results
        }
        
    except Exception as e:
        print(f"✗ Fatal error in pipeline: {e}")
        raise


# Single task that does everything
run_pipeline_task = PythonOperator(
    task_id='run_complete_pipeline',
    python_callable=run_complete_pipeline,
    dag=dag,
    execution_timeout=timedelta(hours=2),  # 2 hour timeout
)

# This is the only task - it does everything
run_pipeline_task

