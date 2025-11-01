#!/bin/bash

# Upload GeoJSON Files to S3
# This script uploads all GeoJSON files from the data directory to the S3 bucket

set -e

# Configuration
ENVIRONMENT="${1:-dev}"
PROJECT_NAME="co2-analysis"

echo "🚀 Uploading GeoJSON files to S3 for environment: $ENVIRONMENT"

# Get bucket name from CloudFormation stack outputs
BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name StorageStack \
  --query "Stacks[0].Outputs[?OutputKey=='GeoJsonBucketName'].OutputValue" \
  --output text)

if [ -z "$BUCKET_NAME" ]; then
  echo "❌ Error: Could not retrieve GeoJSON bucket name from CloudFormation"
  echo "   Make sure StorageStack is deployed"
  exit 1
fi

echo "📦 Target bucket: $BUCKET_NAME"

# Check if data directory exists
if [ ! -d "../data/geojson" ]; then
  echo "⚠️  Warning: data/geojson directory not found"
  echo "   Creating example directory structure..."
  mkdir -p ../data/geojson
  echo "   Please add your GeoJSON files to data/geojson/"
  exit 0
fi

# Upload files
echo "📤 Uploading GeoJSON files..."
aws s3 sync ../data/geojson/ s3://$BUCKET_NAME/data/geojson/ \
  --exclude "*.DS_Store" \
  --exclude "*.git*" \
  --content-type "application/geo+json" \
  --cache-control "max-age=3600"

echo "✅ GeoJSON files uploaded successfully!"
echo ""
echo "📊 Files in bucket:"
aws s3 ls s3://$BUCKET_NAME/data/geojson/ --recursive

# Invalidate CloudFront cache
DISTRIBUTION_ID=$(aws cloudformation describe-stacks \
  --stack-name FrontendStack \
  --query "Stacks[0].Outputs[?OutputKey=='DistributionId'].OutputValue" \
  --output text)

if [ -n "$DISTRIBUTION_ID" ]; then
  echo ""
  echo "🔄 Invalidating CloudFront cache..."
  aws cloudfront create-invalidation \
    --distribution-id $DISTRIBUTION_ID \
    --paths "/data/geojson/*" \
    > /dev/null
  echo "✅ CloudFront cache invalidated"
fi

echo ""
echo "🎉 Deployment complete!"
