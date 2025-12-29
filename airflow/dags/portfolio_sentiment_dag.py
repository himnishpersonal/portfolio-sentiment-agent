"""
Airflow DAG for Portfolio Sentiment Intelligence Agent.

This DAG runs daily at 8am EST (1pm UTC) on weekdays to analyze
portfolio sentiment and send email reports to users.
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
    'portfolio_sentiment_daily',
    default_args=default_args,
    description='Daily portfolio sentiment analysis and email reports',
    schedule_interval='0 13 * * 1-5',  # 8am EST (1pm UTC) on weekdays
    catchup=False,
    tags=['portfolio', 'sentiment', 'ml', 'automated'],
    max_active_runs=1,
)


def get_active_users(**context):
    """Get list of active users from database.
    
    Returns:
        List of user IDs to process.
    """
    try:
        with db_manager.get_session() as session:
            users = session.query(User).all()
            user_ids = [user.id for user in users]
            
            if not user_ids:
                print("No users found in database")
                return []
            
            print(f"Found {len(user_ids)} users to process: {user_ids}")
            return user_ids
    except Exception as e:
        print(f"Error fetching users: {e}")
        raise


def run_pipeline_for_user(user_id: int, **context):
    """Run sentiment pipeline for a single user.
    
    Args:
        user_id: User ID to process.
    """
    try:
        print(f"Starting pipeline for user {user_id}")
        orchestrator = Orchestrator()
        result = orchestrator.run(user_id)
        
        if result.get("email_sent"):
            print(f"✓ Successfully completed pipeline for user {user_id}")
            return {"user_id": user_id, "status": "success", "email_sent": True}
        else:
            print(f"⚠ Pipeline completed for user {user_id} but email may not have been sent")
            return {"user_id": user_id, "status": "warning", "email_sent": False}
            
    except Exception as e:
        print(f"✗ Failed to process user {user_id}: {e}")
        raise


def process_user_task_factory(user_id: int):
    """Factory function to create task for processing a user.
    
    Args:
        user_id: User ID to process.
        
    Returns:
        PythonOperator task.
    """
    return PythonOperator(
        task_id=f'process_user_{user_id}',
        python_callable=run_pipeline_for_user,
        op_kwargs={'user_id': user_id},
        pool='sentiment_pool',  # Limit concurrent executions
        pool_slots=1,
    )


# Task 1: Verify database connection
verify_db = BashOperator(
    task_id='verify_database_connection',
    bash_command='python -c "from db.connection import db_manager; assert db_manager.test_connection(), \'Database connection failed\'; print(\'✓ Database connection successful\')"',
    dag=dag,
)

# Task 2: Get active users
get_users = PythonOperator(
    task_id='get_active_users',
    python_callable=get_active_users,
    dag=dag,
)

# Task 3: Process each user (dynamic task creation)
# This will be handled by TaskGroup or we'll use a different approach
from airflow.utils.task_group import TaskGroup

def create_user_processing_tasks(**context):
    """Create dynamic tasks for each user."""
    ti = context['ti']
    user_ids = ti.xcom_pull(task_ids='get_active_users')
    
    if not user_ids:
        print("No users to process")
        return
    
    with TaskGroup("process_users", dag=dag) as process_group:
        for user_id in user_ids:
            task = PythonOperator(
                task_id=f'process_user_{user_id}',
                python_callable=run_pipeline_for_user,
                op_kwargs={'user_id': user_id},
                pool='sentiment_pool',
                pool_slots=1,
            )
    
    return process_group


# Alternative: Use dynamic task mapping (Airflow 2.3+)
def process_users_dynamic(**context):
    """Process all users dynamically."""
    ti = context['ti']
    user_ids = ti.xcom_pull(task_ids='get_active_users')
    
    if not user_ids:
        print("No users to process")
        return
    
    results = []
    for user_id in user_ids:
        try:
            result = run_pipeline_for_user(user_id=user_id, **context)
            results.append(result)
        except Exception as e:
            print(f"Failed to process user {user_id}: {e}")
            results.append({"user_id": user_id, "status": "failed", "error": str(e)})
    
    return results


# Task 3: Process all users
process_all_users = PythonOperator(
    task_id='process_all_users',
    python_callable=process_users_dynamic,
    dag=dag,
)

# Task 4: Generate summary report
def generate_summary(**context):
    """Generate execution summary."""
    ti = context['ti']
    results = ti.xcom_pull(task_ids='process_all_users')
    
    if not results:
        print("No results to summarize")
        return
    
    success_count = sum(1 for r in results if r.get('status') == 'success')
    failure_count = sum(1 for r in results if r.get('status') == 'failed')
    warning_count = sum(1 for r in results if r.get('status') == 'warning')
    
    summary = f"""
    Pipeline Execution Summary:
    ===========================
    Total Users: {len(results)}
    Successful: {success_count}
    Warnings: {warning_count}
    Failed: {failure_count}
    ===========================
    """
    
    print(summary)
    return summary


summary_task = PythonOperator(
    task_id='generate_summary',
    python_callable=generate_summary,
    dag=dag,
)

# Define task dependencies
verify_db >> get_users >> process_all_users >> summary_task

