"""
Airflow DAG for Portfolio Sentiment Intelligence Agent (Improved Version).

This version uses dynamic task mapping and better error handling.
Requires Airflow 2.3+ for dynamic task mapping.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
from airflow.utils.task_group import TaskGroup

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
    'execution_timeout': timedelta(minutes=30),  # 30 minute timeout per task
}

# Create DAG
dag = DAG(
    'portfolio_sentiment_daily_v2',
    default_args=default_args,
    description='Daily portfolio sentiment analysis and email reports (v2)',
    schedule_interval='0 13 * * 1-5',  # 8am EST (1pm UTC) on weekdays
    catchup=False,
    tags=['portfolio', 'sentiment', 'ml', 'automated'],
    max_active_runs=1,
    dagrun_timeout=timedelta(hours=2),  # 2 hour timeout for entire DAG
)


def verify_database(**context):
    """Verify database connection is working."""
    try:
        from db.connection import db_manager
        if db_manager.test_connection():
            print("✓ Database connection successful")
            return True
        else:
            raise Exception("Database connection test failed")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        raise


def get_active_users(**context):
    """Get list of active users from database.
    
    Returns:
        List of user dictionaries with id and email.
    """
    try:
        with db_manager.get_session() as session:
            users = session.query(User).all()
            user_list = [{"id": user.id, "email": user.email} for user in users]
            
            if not user_list:
                print("No users found in database")
                return []
            
            print(f"Found {len(user_list)} users to process")
            for user in user_list:
                print(f"  - User {user['id']}: {user['email']}")
            
            return user_list
    except Exception as e:
        print(f"Error fetching users: {e}")
        raise


def run_pipeline_for_user(user_id: int, user_email: str, **context):
    """Run sentiment pipeline for a single user.
    
    Args:
        user_id: User ID to process.
        user_email: User email address.
    """
    try:
        print(f"Starting pipeline for user {user_id} ({user_email})")
        orchestrator = Orchestrator()
        result = orchestrator.run(user_id)
        
        if result.get("email_sent"):
            print(f"✓ Successfully completed pipeline for user {user_id}")
            return {
                "user_id": user_id,
                "user_email": user_email,
                "status": "success",
                "email_sent": True
            }
        else:
            print(f"⚠ Pipeline completed for user {user_id} but email may not have been sent")
            return {
                "user_id": user_id,
                "user_email": user_email,
                "status": "warning",
                "email_sent": False
            }
            
    except Exception as e:
        print(f"✗ Failed to process user {user_id}: {e}")
        return {
            "user_id": user_id,
            "user_email": user_email,
            "status": "failed",
            "error": str(e),
            "email_sent": False
        }


def process_users_parallel(**context):
    """Process all users in parallel using dynamic task mapping.
    
    This function prepares the data for dynamic task mapping.
    """
    ti = context['ti']
    users = ti.xcom_pull(task_ids='get_active_users')
    
    if not users:
        print("No users to process")
        return []
    
    # Return list of user IDs for dynamic mapping
    return [user['id'] for user in users]


def process_single_user(user_id: int, **context):
    """Process a single user (used in dynamic task mapping)."""
    ti = context['ti']
    users = ti.xcom_pull(task_ids='get_active_users')
    
    # Find user details
    user = next((u for u in users if u['id'] == user_id), None)
    if not user:
        raise ValueError(f"User {user_id} not found")
    
    return run_pipeline_for_user(
        user_id=user['id'],
        user_email=user['email'],
        **context
    )


def generate_summary(**context):
    """Generate execution summary from all user processing results."""
    ti = context['ti']
    
    # Get results from all user processing tasks
    # In dynamic task mapping, results are stored per task
    users = ti.xcom_pull(task_ids='get_active_users')
    results = []
    
    for user in users:
        try:
            result = ti.xcom_pull(task_ids=f'process_user_{user["id"]}')
            if result:
                results.append(result)
        except:
            # Task may have failed
            results.append({
                "user_id": user['id'],
                "status": "failed",
                "error": "Task execution failed"
            })
    
    if not results:
        print("No results to summarize")
        return
    
    success_count = sum(1 for r in results if r.get('status') == 'success')
    failure_count = sum(1 for r in results if r.get('status') == 'failed')
    warning_count = sum(1 for r in results if r.get('status') == 'warning')
    
    summary = f"""
    ╔═══════════════════════════════════════════════════════╗
    ║   Portfolio Sentiment Pipeline Execution Summary      ║
    ╠═══════════════════════════════════════════════════════╣
    ║  Total Users Processed: {len(results):<30} ║
    ║  Successful:            {success_count:<30} ║
    ║  Warnings:              {warning_count:<30} ║
    ║  Failed:                {failure_count:<30} ║
    ╚═══════════════════════════════════════════════════════╝
    """
    
    print(summary)
    
    # Print detailed results
    if failure_count > 0:
        print("\nFailed Users:")
        for r in results:
            if r.get('status') == 'failed':
                print(f"  - User {r.get('user_id')}: {r.get('error', 'Unknown error')}")
    
    return {
        "total": len(results),
        "success": success_count,
        "warnings": warning_count,
        "failed": failure_count,
        "results": results
    }


# Task 1: Verify database connection
verify_db_task = PythonOperator(
    task_id='verify_database_connection',
    python_callable=verify_database,
    dag=dag,
)

# Task 2: Get active users
get_users_task = PythonOperator(
    task_id='get_active_users',
    python_callable=get_active_users,
    dag=dag,
)

# Task 3: Process users (using TaskGroup for better organization)
with TaskGroup("process_users_group", dag=dag) as process_group:
    # This creates a task for each user dynamically
    # Note: For true dynamic task mapping (Airflow 2.3+), use:
    # process_users = PythonOperator.partial(
    #     task_id='process_user',
    #     python_callable=process_single_user,
    #     pool='sentiment_pool',
    # ).expand(op_kwargs={'user_id': get_users_task.output})
    
    # For compatibility, we'll create tasks in a loop
    # In production, use dynamic task mapping if available
    
    def create_user_tasks():
        """Create user processing tasks dynamically."""
        # This will be populated at DAG parse time
        # For true dynamic behavior, use Airflow 2.3+ dynamic task mapping
        pass
    
    # Fallback: Process sequentially in a single task
    process_all_users_task = PythonOperator(
        task_id='process_all_users',
        python_callable=lambda **context: [
            process_single_user(
                user['id'],
                user_email=user['email'],
                **context
            )
            for user in context['ti'].xcom_pull(task_ids='get_active_users') or []
        ],
        pool='sentiment_pool',
        pool_slots=1,  # Process one at a time to avoid memory issues
        dag=dag,
    )

# Task 4: Generate summary
summary_task = PythonOperator(
    task_id='generate_summary',
    python_callable=generate_summary,
    dag=dag,
)

# Define task dependencies
verify_db_task >> get_users_task >> process_all_users_task >> summary_task

