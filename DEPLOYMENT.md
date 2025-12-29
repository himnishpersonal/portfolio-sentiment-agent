# Deployment Guide - Google Cloud Composer (Airflow)

This guide covers deploying the Portfolio Sentiment Intelligence Agent to Google Cloud Composer (managed Airflow).

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Deploying the DAG](#deploying-the-dag)
4. [Configuration](#configuration)
5. [Monitoring](#monitoring)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Accounts & Services

1. **Google Cloud Platform Account** with billing enabled
2. **Cloud Composer** API enabled
3. **Cloud SQL** or external PostgreSQL database
4. **Secret Manager** API enabled (for secure credential storage)
5. **Cloud Storage** bucket (auto-created by Composer)

### Required API Keys

- NewsAPI key
- Finnhub key
- SendGrid API key
- Anthropic or OpenAI API key

## Initial Setup

### 1. Create GCP Project

```bash
# Set your project ID
export PROJECT_ID="your-project-id"
export REGION="us-central1"  # or your preferred region

# Create project (if new)
gcloud projects create ${PROJECT_ID}

# Set as current project
gcloud config set project ${PROJECT_ID}

# Enable billing (required for Composer)
# Do this via GCP Console: https://console.cloud.google.com/billing
```

### 2. Enable Required APIs

```bash
# Enable Composer API
gcloud services enable composer.googleapis.com

# Enable Secret Manager API
gcloud services enable secretmanager.googleapis.com

# Enable Cloud SQL Admin API (if using Cloud SQL)
gcloud services enable sqladmin.googleapis.com
```

### 3. Create Cloud Composer Environment

```bash
# Create Composer environment
gcloud composer environments create portfolio-sentiment-env \
    --location ${REGION} \
    --python-version 3 \
    --image-version composer-2.7.0-airflow-2.7.0 \
    --machine-type n1-standard-2 \
    --node-count 3 \
    --disk-size 30GB \
    --enable-ip-alias \
    --network default \
    --subnetwork default
```

**Note:** This takes 20-30 minutes. For production, consider:
- Larger machine types (`n1-standard-4` or `n1-standard-8`) for ML workloads
- More nodes for better parallelism
- Larger disk size (50GB+) for model caching

### 4. Set Up Database

#### Option A: Cloud SQL (Recommended)

```bash
# Create Cloud SQL instance
gcloud sql instances create portfolio-sentiment-db \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=${REGION} \
    --root-password=YOUR_PASSWORD

# Create database
gcloud sql databases create portfolio_sentiment \
    --instance=portfolio-sentiment-db

# Get connection name
gcloud sql instances describe portfolio-sentiment-db \
    --format="get(connectionName)"
```

#### Option B: External PostgreSQL

Use your existing PostgreSQL database (Supabase, RDS, etc.). Ensure it's accessible from Composer's network.

### 5. Store Secrets in Secret Manager

```bash
# Store database URL
echo -n "postgresql://user:pass@host:5432/db" | \
    gcloud secrets create database-url \
    --data-file=- \
    --replication-policy="automatic"

# Store API keys
echo -n "your-newsapi-key" | \
    gcloud secrets create newsapi-key \
    --data-file=- \
    --replication-policy="automatic"

echo -n "your-finnhub-key" | \
    gcloud secrets create finnhub-key \
    --data-file=- \
    --replication-policy="automatic"

echo -n "your-sendgrid-key" | \
    gcloud secrets create sendgrid-key \
    --data-file=- \
    --replication-policy="automatic"

echo -n "your-anthropic-key" | \
    gcloud secrets create anthropic-key \
    --data-file=- \
    --replication-policy="automatic"

echo -n "your-email@example.com" | \
    gcloud secrets create email-from \
    --data-file=- \
    --replication-policy="automatic"
```

### 6. Grant Composer Access to Secrets

```bash
# Get Composer service account
COMPOSER_SA=$(gcloud composer environments describe portfolio-sentiment-env \
    --location ${REGION} \
    --format="get(config.nodeConfig.serviceAccount)")

# Grant Secret Manager Secret Accessor role
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${COMPOSER_SA}" \
    --role="roles/secretmanager.secretAccessor"
```

## Deploying the DAG

### Method 1: Automated Deployment Script

```bash
# Set environment variables
export GCP_PROJECT_ID=${PROJECT_ID}
export COMPOSER_ENV=portfolio-sentiment-env
export GCP_REGION=${REGION}

# Run deployment script
./airflow/deploy.sh
```

### Method 2: Manual Deployment

```bash
# Get Composer bucket name
COMPOSER_BUCKET=$(gcloud composer environments describe portfolio-sentiment-env \
    --location ${REGION} \
    --format="get(config.dagGcsPrefix)" | cut -d'/' -f3)

echo "Composer bucket: ${COMPOSER_BUCKET}"

# Upload DAG files
gsutil -m cp -r airflow/dags/* gs://${COMPOSER_BUCKET}/dags/

# Upload application code
gsutil -m cp -r agents gs://${COMPOSER_BUCKET}/dags/
gsutil -m cp -r services gs://${COMPOSER_BUCKET}/dags/
gsutil -m cp -r db gs://${COMPOSER_BUCKET}/dags/
gsutil -m cp -r config gs://${COMPOSER_BUCKET}/dags/
gsutil -m cp requirements.txt gs://${COMPOSER_BUCKET}/dags/
gsutil -m cp main.py gs://${COMPOSER_BUCKET}/dags/
gsutil -m cp -r scripts gs://${COMPOSER_BUCKET}/dags/
```

### 3. Install Python Dependencies

```bash
# Create requirements file for Composer
cat > /tmp/composer-requirements.txt << 'EOF'
python-dotenv>=1.0.0
pydantic>=2.5.0
sqlalchemy>=2.0.23
psycopg2-binary>=2.9.9
torch>=2.1.0
transformers>=4.35.0
sentencepiece>=0.1.99
requests>=2.31.0
sendgrid>=6.11.0
anthropic>=0.18.0
openai>=1.6.0
langgraph>=0.0.20
langchain>=0.1.0
langchain-core>=0.1.0
pyyaml>=6.0.1
python-dateutil>=2.8.2
google-cloud-secret-manager>=2.16.0
EOF

# Update Composer environment with dependencies
gcloud composer environments update portfolio-sentiment-env \
    --location ${REGION} \
    --update-pypi-packages-from-file /tmp/composer-requirements.txt
```

**Important:** Installing PyTorch and transformers can take 20-30 minutes and may require larger machine types.

## Configuration

### Environment Variables

Set environment variables in Composer:

```bash
gcloud composer environments update portfolio-sentiment-env \
    --location ${REGION} \
    --update-env-variables \
    GCP_PROJECT_ID=${PROJECT_ID},\
    LLM_PROVIDER=anthropic,\
    EMAIL_FROM_NAME="Portfolio Sentiment Agent"
```

### Airflow Variables (Alternative)

Set via Airflow UI:
1. Open Airflow web UI
2. Go to Admin → Variables
3. Add variables:
   - `DATABASE_URL`: Your database connection string
   - `NEWSAPI_KEY`: Your NewsAPI key
   - etc.

### Database Connection

If using Cloud SQL, configure Cloud SQL Proxy:

```bash
# Add Cloud SQL Proxy to Composer environment
gcloud composer environments update portfolio-sentiment-env \
    --location ${REGION} \
    --update-env-variables \
    CLOUD_SQL_CONNECTION_NAME="project:region:instance"
```

## Monitoring

### Access Airflow UI

```bash
# Get Airflow web server URL
gcloud composer environments describe portfolio-sentiment-env \
    --location ${REGION} \
    --format="get(config.airflowUri)"
```

Open the URL in your browser and login with your GCP account.

### View DAG Logs

```bash
# View logs for a specific task
gcloud composer environments run portfolio-sentiment-env \
    --location ${REGION} \
    logs read \
    --dag-id portfolio_sentiment_daily_simple \
    --task-id run_complete_pipeline \
    --limit 100
```

### Monitor in Cloud Console

1. Go to [Composer Environments](https://console.cloud.google.com/composer/environments)
2. Click on your environment
3. View metrics, logs, and DAG runs

### Set Up Alerts

```bash
# Create alert policy for DAG failures
gcloud alpha monitoring policies create \
    --notification-channels=CHANNEL_ID \
    --display-name="Portfolio Sentiment DAG Failed" \
    --condition-display-name="DAG failure" \
    --condition-threshold-value=1 \
    --condition-threshold-duration=300s
```

## Troubleshooting

### DAG Not Appearing

1. **Check DAG files are uploaded:**
   ```bash
   gsutil ls gs://${COMPOSER_BUCKET}/dags/
   ```

2. **Check for syntax errors:**
   ```bash
   python -m py_compile airflow/dags/portfolio_sentiment_dag_simple.py
   ```

3. **Check Airflow logs:**
   ```bash
   gcloud composer environments run portfolio-sentiment-env \
       --location ${REGION} \
       logs read \
       --limit 50
   ```

### Import Errors

1. **Verify dependencies:**
   ```bash
   gcloud composer environments describe portfolio-sentiment-env \
       --location ${REGION} \
       --format="get(config.softwareConfig.pypiPackages)"
   ```

2. **Reinstall dependencies if needed**

### Database Connection Issues

1. **If using Cloud SQL:**
   - Verify Cloud SQL Proxy is configured
   - Check firewall rules allow Composer access
   - Verify connection name format: `project:region:instance`

2. **If using external database:**
   - Ensure database is accessible from Composer's network
   - Check firewall/security group rules
   - Verify credentials in Secret Manager

### Memory Issues

If ML inference fails due to memory:

1. **Increase machine type:**
   ```bash
   gcloud composer environments update portfolio-sentiment-env \
       --location ${REGION} \
       --machine-type n1-standard-4
   ```

2. **Reduce batch size** in `config/settings.py`:
   ```python
   SENTIMENT_BATCH_SIZE = 4  # Reduce from 8
   ```

3. **Process users sequentially** (use `portfolio_sentiment_dag_simple.py`)

### Slow Execution

1. **Increase node count** for better parallelism
2. **Use larger machine types** for faster ML inference
3. **Enable model caching** (models persist between runs)

## Cost Optimization

### Estimated Monthly Costs

- **Composer Environment:** ~$300-500/month (3 nodes, n1-standard-2)
- **Cloud SQL:** ~$10-50/month (db-f1-micro to db-n1-standard-1)
- **Storage:** ~$5-10/month
- **Network:** ~$10-20/month

**Total:** ~$325-580/month

### Cost Reduction Tips

1. **Use preemptible nodes** (50% cheaper, but can be interrupted)
2. **Schedule during off-peak hours** if timing is flexible
3. **Use smaller machine types** if processing few users
4. **Scale down** when not in use (pause DAG during weekends)
5. **Use Cloud SQL Proxy** instead of public IP (reduces network costs)

## Production Checklist

- [ ] Composer environment created with appropriate sizing
- [ ] Database configured and accessible
- [ ] All secrets stored in Secret Manager
- [ ] Composer service account has Secret Manager access
- [ ] DAG files uploaded to Composer bucket
- [ ] Python dependencies installed
- [ ] Environment variables configured
- [ ] DAG appears in Airflow UI
- [ ] Test run completed successfully
- [ ] Monitoring and alerts configured
- [ ] Documentation updated with environment-specific details

## Next Steps

1. **Test the DAG manually** in Airflow UI before enabling schedule
2. **Monitor first few runs** closely
3. **Set up alerts** for failures
4. **Optimize** based on execution times and costs
5. **Scale** as user base grows

## Support

For issues:
- Check [Cloud Composer documentation](https://cloud.google.com/composer/docs)
- Review Airflow logs in Cloud Logging
- Check DAG execution history in Airflow UI
- Review Composer environment health in GCP Console

