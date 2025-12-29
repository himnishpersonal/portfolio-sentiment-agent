#!/bin/bash
# Deployment script for Google Cloud Composer (Airflow)

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-your-project-id}"
COMPOSER_ENV="${COMPOSER_ENV:-portfolio-sentiment-env}"
REGION="${GCP_REGION:-us-central1}"
DAGS_BUCKET="gs://${PROJECT_ID}-composer-dags"

echo "🚀 Deploying Portfolio Sentiment Agent to Google Cloud Composer"
echo "Project: ${PROJECT_ID}"
echo "Environment: ${COMPOSER_ENV}"
echo "Region: ${REGION}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install Google Cloud SDK."
    exit 1
fi

# Check if gsutil is installed
if ! command -v gsutil &> /dev/null; then
    echo "❌ gsutil not found. Please install Google Cloud SDK."
    exit 1
fi

# Set project
echo "📋 Setting GCP project..."
gcloud config set project ${PROJECT_ID}

# Get Composer environment details
echo "🔍 Getting Composer environment details..."
COMPOSER_BUCKET=$(gcloud composer environments describe ${COMPOSER_ENV} \
    --location ${REGION} \
    --format="get(config.dagGcsPrefix)" | cut -d'/' -f3)

if [ -z "$COMPOSER_BUCKET" ]; then
    echo "❌ Could not find Composer environment: ${COMPOSER_ENV}"
    exit 1
fi

DAGS_FOLDER="gs://${COMPOSER_BUCKET}/dags"
PLUGINS_FOLDER="gs://${COMPOSER_BUCKET}/plugins"

echo "✓ Found Composer bucket: ${COMPOSER_BUCKET}"
echo ""

# Create temporary directory for deployment
TEMP_DIR=$(mktemp -d)
echo "📦 Preparing deployment package..."

# Copy DAG files
mkdir -p ${TEMP_DIR}/dags
cp -r airflow/dags/* ${TEMP_DIR}/dags/
cp -r agents ${TEMP_DIR}/dags/
cp -r services ${TEMP_DIR}/dags/
cp -r db ${TEMP_DIR}/dags/
cp -r config ${TEMP_DIR}/dags/
cp requirements.txt ${TEMP_DIR}/dags/
cp main.py ${TEMP_DIR}/dags/
cp -r scripts ${TEMP_DIR}/dags/

# Copy plugins
mkdir -p ${TEMP_DIR}/plugins
cp -r airflow/plugins/* ${TEMP_DIR}/plugins/

echo "✓ Files prepared"
echo ""

# Upload DAGs to Composer
echo "📤 Uploading DAGs to ${DAGS_FOLDER}..."
gsutil -m rsync -r ${TEMP_DIR}/dags ${DAGS_FOLDER}

# Upload plugins
echo "📤 Uploading plugins to ${PLUGINS_FOLDER}..."
gsutil -m rsync -r ${TEMP_DIR}/plugins ${PLUGINS_FOLDER}

# Cleanup
rm -rf ${TEMP_DIR}

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Verify DAG appears in Airflow UI"
echo "2. Check that all dependencies are installed"
echo "3. Set up environment variables in Composer"
echo "4. Test the DAG manually before enabling schedule"
echo ""
echo "Airflow UI: https://console.cloud.google.com/composer/environments/${COMPOSER_ENV}/monitoring?project=${PROJECT_ID}"

