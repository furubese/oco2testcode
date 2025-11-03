#!/bin/bash

###############################################################################
# GeoJSON Files Upload Script
#
# This script uploads all GeoJSON files to the S3 GeoJSON bucket created by
# the StorageStack. It should be run after `cdk deploy`.
#
# Usage:
#   ./upload-geojson-files.sh [environment] [source-directory]
#
# Example:
#   ./upload-geojson-files.sh dev ./data/geojson
#   ./upload-geojson-files.sh prod ../geojson-data
#
# Environment variables:
#   AWS_REGION - AWS region (default: us-east-1)
###############################################################################

set -e

# Default values
ENVIRONMENT="${1:-dev}"
SOURCE_DIR="${2:-../../data/geojson}"
AWS_REGION="${AWS_REGION:-us-east-1}"
PROJECT_NAME="co2-analysis"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    log_error "AWS CLI is not installed. Please install it first."
    exit 1
fi

log_info "GeoJSON Upload Script"
log_info "Environment: ${ENVIRONMENT}"
log_info "Source Directory: ${SOURCE_DIR}"
log_info "AWS Region: ${AWS_REGION}"
log_info ""

# Check if source directory exists
if [ ! -d "$SOURCE_DIR" ]; then
    log_error "Source directory not found: ${SOURCE_DIR}"
    log_info ""
    log_info "Please create the directory and add your GeoJSON files:"
    log_info "  mkdir -p ${SOURCE_DIR}"
    log_info "  cp your-file.geojson ${SOURCE_DIR}/"
    log_info ""
    log_info "Expected GeoJSON file format (based on sample_calendar.html):"
    log_info "  - 2020-12.geojson"
    log_info "  - 2021-03.geojson"
    log_info "  - 2023-01.geojson to 2023-10.geojson"
    exit 1
fi

# Fetch S3 bucket name from Parameter Store
log_info "Fetching GeoJSON S3 bucket name from Parameter Store..."
GEOJSON_BUCKET=$(aws ssm get-parameter \
    --name "/${PROJECT_NAME}/${ENVIRONMENT}/frontend/s3/geojson-bucket-name" \
    --region "${AWS_REGION}" \
    --query 'Parameter.Value' \
    --output text 2>/dev/null || echo "")

if [ -z "$GEOJSON_BUCKET" ]; then
    log_error "GeoJSON bucket not found in Parameter Store."
    log_info "Make sure you have deployed the CDK stack first:"
    log_info "  cd cdk && cdk deploy --context environment=${ENVIRONMENT}"
    exit 1
fi

log_info "Target S3 Bucket: ${GEOJSON_BUCKET}"

# Count GeoJSON files
GEOJSON_COUNT=$(find "$SOURCE_DIR" -name "*.geojson" -type f 2>/dev/null | wc -l)

if [ "$GEOJSON_COUNT" -eq 0 ]; then
    log_warn "No GeoJSON files found in ${SOURCE_DIR}"
    log_info ""
    log_info "Expected files (based on sample_calendar.html):"
    log_info "  - 2020-12.geojson"
    log_info "  - 2021-03.geojson"
    log_info "  - 2023-01.geojson to 2023-10.geojson"
    exit 1
fi

log_info "Found ${GEOJSON_COUNT} GeoJSON file(s) to upload"
log_info ""

# Upload files to S3
log_info "Uploading GeoJSON files to S3..."

# Use AWS S3 sync for efficient upload
aws s3 sync "$SOURCE_DIR" "s3://${GEOJSON_BUCKET}/data/geojson/" \
    --exclude "*" \
    --include "*.geojson" \
    --region "${AWS_REGION}" \
    --content-type "application/geo+json" \
    --metadata-directive REPLACE

log_info "✓ Successfully uploaded GeoJSON files to S3"

# List uploaded files
log_info ""
log_info "Uploaded files:"
aws s3 ls "s3://${GEOJSON_BUCKET}/data/geojson/" --region "${AWS_REGION}" | grep ".geojson"

# Invalidate CloudFront cache if distribution exists
log_info ""
log_info "Invalidating CloudFront cache..."
DISTRIBUTION_ID=$(aws ssm get-parameter \
    --name "/${PROJECT_NAME}/${ENVIRONMENT}/frontend/cloudfront/distribution-id" \
    --region "${AWS_REGION}" \
    --query 'Parameter.Value' \
    --output text 2>/dev/null || echo "")

if [ -n "$DISTRIBUTION_ID" ]; then
    aws cloudfront create-invalidation \
        --distribution-id "${DISTRIBUTION_ID}" \
        --paths "/data/geojson/*" \
        --region "${AWS_REGION}" > /dev/null
    log_info "✓ CloudFront cache invalidated for /data/geojson/*"
else
    log_warn "CloudFront distribution not found. Skipping cache invalidation."
fi

log_info ""
log_info "✓ GeoJSON upload complete!"
log_info ""
log_info "Files are now accessible at:"
log_info "  https://{cloudfront-domain}/data/geojson/{filename}.geojson"
log_info ""
log_info "To verify uploads:"
log_info "  aws s3 ls s3://${GEOJSON_BUCKET}/data/geojson/ --region ${AWS_REGION}"
