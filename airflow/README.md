# Google Cloud Composer (Airflow) Deployment

This directory contains the Airflow DAG and deployment configuration for running the Portfolio Sentiment Agent on Google Cloud Composer.

## Architecture

```
Google Cloud Composer (Managed Airflow)
    ↓
Airflow DAG (portfolio_sentiment_daily)
    ↓
    ├→ Task 1: Verify Database Connection
    ├→ Task 2: Get Active Users
    ├→ Task 3: Process All Users (parallel)
    └→ Task 4: Generate Summary Report
```

## Prerequisites

1. **Google Cloud Project** with billing enabled
2. **Cloud Composer Environment** created
3. **Cloud SQL** or **Cloud SQL Proxy** for PostgreSQL
4. **Secret Manager** for API keys (recommended)
5. **Cloud Storage** bucket for DAGs (auto-created by Composer)

## Setup Instructions

### 1. Create Cloud Composer Environment

```bash
gcloud composer environments create portfolio-sentiment-env \
    --location us-central1 \
    --python-version 3 \
    --image-version composer-2.7.0-airflow-2.7.0 \
    --machine-type n1-standard-2 \
    --node-count 3 \
    --disk-size 30GB
```

### 2. Store Secrets in Secret Manager

```bash
# Set your project ID
export PROJECT_ID=your-project-id

# Store secrets
echo -n "your-database-url" | gcloud secrets create database-url --data-file=-
echo -n "your-newsapi-key" | gcloud secrets create newsapi-key --data-file=-
echo -n "your-finnhub-key" | gcloud secrets create finnhub-key --data-file=-
echo -n "your-sendgrid-key" | gcloud secrets create sendgrid-key --data-file=-
echo -n "your-anthropic-key" | gcloud secrets create anthropic-key --data-file=-
echo -n "your-email-from" | gcloud secrets create email-from --data-file=-
```

### 3. Update DAG to Use Secrets

The DAG will need to be updated to fetch secrets from Secret Manager. See `airflow/dags/portfolio_sentiment_dag.py` for the implementation.

### 4. Install Python Dependencies

Add dependencies to Composer environment:

```bash
# Create requirements file
cat > /tmp/requirements.txt << EOF
# Core dependencies
python-dotenv>=1.0.0
pydantic>=2.5.0
sqlalchemy>=2.0.23
psycopg2-binary>=2.9.9

# ML dependencies
torch>=2.1.0
transformers>=4.35.0
sentencepiece>=0.1.99

# API clients
requests>=2.31.0
sendgrid>=6.11.0
anthropic>=0.18.0
openai>=1.6.0

# LangGraph
langgraph>=0.0.20
langchain>=0.1.0
langchain-core>=0.1.0

# Utilities
pyyaml>=6.0.1
python-dateutil>=2.8.2

# Google Cloud
google-cloud-secret-manager>=2.16.0
EOF

# Update Composer environment
gcloud composer environments update portfolio-sentiment-env \
    --location us-central1 \
    --update-pypi-packages-from-file /tmp/requirements.txt
```

**Note:** Installing PyTorch and transformers may take 15-30 minutes and require larger machine types.

### 5. Deploy DAG

```bash
# Set environment variables
export GCP_PROJECT_ID=your-project-id
export COMPOSER_ENV=portfolio-sentiment-env
export GCP_REGION=us-central1

# Make deploy script executable
chmod +x airflow/deploy.sh

# Run deployment
./airflow/deploy.sh
```

Or manually:

```bash
# Get Composer bucket
COMPOSER_BUCKET=$(gcloud composer environments describe portfolio-sentiment-env \
    --location us-central1 \
    --format="get(config.dagGcsPrefix)" | cut -d'/' -f3)

# Upload DAG
gsutil cp -r airflow/dags/* gs://${COMPOSER_BUCKET}/dags/
gsutil cp -r agents gs://${COMPOSER_BUCKET}/dags/
gsutil cp -r services gs://${COMPOSER_BUCKET}/dags/
gsutil cp -r db gs://${COMPOSER_BUCKET}/dags/
gsutil cp -r config gs://${COMPOSER_BUCKET}/dags/
gsutil cp requirements.txt gs://${COMPOSER_BUCKET}/dags/
```

## Configuration

### Environment Variables

Set in Composer environment:

```bash
gcloud composer environments update portfolio-sentiment-env \
    --location us-central1 \
    --update-env-variables \
    DATABASE_URL=postgresql://user:pass@host:5432/db,\
    NEWSAPI_KEY=your-key,\
    FINNHUB_KEY=your-key,\
    SENDGRID_API_KEY=your-key,\
    LLM_PROVIDER=anthropic,\
    ANTHROPIC_API_KEY=your-key,\
    EMAIL_FROM=your-email@example.com
```

### Airflow Variables

Set via Airflow UI or CLI:

```bash
# Via CLI
gcloud composer environments run portfolio-sentiment-env \
    --location us-central1 \
    variables -- \
    set DATABASE_URL "postgresql://..."
```

## Monitoring

### View DAG in Airflow UI

1. Get Airflow web server URL:
```bash
gcloud composer environments describe portfolio-sentiment-env \
    --location us-central1 \
    --format="get(config.airflowUri)"
```

2. Open URL in browser and login

### Check Logs

```bash
# View DAG logs
gcloud composer environments run portfolio-sentiment-env \
    --location us-central1 \
    logs read \
    --dag-id portfolio_sentiment_daily \
    --task-id process_all_users
```

### Monitor Execution

```bash
# List recent DAG runs
gcloud composer environments run portfolio-sentiment-env \
    --location us-central1 \
    dags list-runs \
    --dag-id portfolio_sentiment_daily \
    --limit 10
```

## Troubleshooting

### DAG Not Appearing

1. Check DAG files are in correct location: `gs://[BUCKET]/dags/`
2. Verify Python syntax is correct
3. Check Airflow logs for import errors

### Import Errors

1. Verify all dependencies are installed in Composer environment
2. Check that modules are in the DAGs folder
3. Ensure `__init__.py` files exist in packages

### Database Connection Issues

1. If using Cloud SQL, ensure Cloud SQL Proxy is configured
2. Check firewall rules allow Composer to access database
3. Verify database credentials in Secret Manager

### Memory Issues

1. Increase Composer machine type:
```bash
gcloud composer environments update portfolio-sentiment-env \
    --location us-central1 \
    --machine-type n1-standard-4
```

2. Reduce batch sizes in sentiment agent

## Cost Optimization

- Use **preemptible nodes** for worker nodes (cheaper)
- Set **max_active_runs=1** to prevent overlapping executions
- Use **pool slots** to limit concurrent ML inference
- Consider **Cloud SQL Proxy** instead of public IP for database

## Security Best Practices

1. **Never commit secrets** - use Secret Manager
2. **Use IAM roles** - grant minimal permissions
3. **Enable VPC** - use private IP for database
4. **Audit logs** - enable Cloud Audit Logs
5. **Network policies** - restrict network access

## Scaling

For high-volume deployments:

1. **Increase node count** in Composer environment
2. **Use Celery executor** (default) for distributed execution
3. **Add worker pools** for different task types
4. **Consider Cloud Run** for ML inference (separate service)

## Support

For issues:
1. Check Airflow logs in Cloud Logging
2. Review DAG execution history in Airflow UI
3. Check Composer environment health in GCP Console

