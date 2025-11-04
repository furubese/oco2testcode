# CDK Deployment Guide

## Quick Start

### 1. Prerequisites Checklist

- [ ] Node.js v18+ installed (`node --version`)
- [ ] AWS CLI v2 installed (`aws --version`)
- [ ] AWS CDK CLI installed (`cdk --version`)
- [ ] AWS credentials configured (`aws configure`)
- [ ] Amazon Bedrock access enabled in us-east-1 region

### 2. Initial Setup (First Time Only)

```bash
# Navigate to CDK directory
cd cdk

# Install Node.js dependencies
npm install

# Configure your environment in cdk.json
# Edit: environmentConfig.dev.account, region, alarmEmail

# Bootstrap CDK in your AWS account/region
cdk bootstrap aws://YOUR-ACCOUNT-ID/us-east-1
```

### 3. Deploy to Development

```bash
# Preview changes
cdk diff --all --context environment=dev

# Deploy all stacks
cdk deploy --all --context environment=dev --require-approval never
```

### 4. Post-Deployment Configuration

```bash
# 1. Verify Bedrock model access
aws bedrock list-foundation-models \
    --region us-east-1 \
    --query 'modelSummaries[?modelId==`amazon.nova-pro-v1:0`]'

# 2. Upload GeoJSON files to S3
# Get bucket name from outputs
BUCKET=$(aws cloudformation describe-stacks \
    --stack-name StorageStack \
    --query 'Stacks[0].Outputs[?OutputKey==`GeoJsonBucketName`].OutputValue' \
    --output text)

# Upload files
aws s3 cp ../data/geojson/ s3://$BUCKET/data/geojson/ --recursive

# 3. Test Lambda with Bedrock
aws lambda invoke \
    --function-name co2-analysis-dev-reasoning-function \
    --payload '{"body": "{\"lat\": 35.6762, \"lon\": 139.6503, \"co2\": 420.5}"}' \
    response.json && cat response.json

# 4. Get CloudFront URL
aws cloudformation describe-stacks \
    --stack-name FrontendStack \
    --query 'Stacks[0].Outputs[?OutputKey==`WebsiteUrl`].OutputValue' \
    --output text
```

### 5. Verify Deployment

```bash
# Test Lambda function
aws lambda invoke \
    --function-name co2-analysis-dev-reasoning-function \
    --payload '{"body": "{\"lat\": 35.6762, \"lon\": 139.6503, \"co2\": 420.5, \"deviation\": 5.0, \"date\": \"2023-01-15\", \"severity\": \"high\", \"zscore\": 2.5}"}' \
    response.json

cat response.json

# Check DynamoDB cache
aws dynamodb scan --table-name co2-analysis-dev-cache --limit 5

# Verify S3 files
aws s3 ls s3://$BUCKET/data/geojson/
```

## Stack Deployment Order

The stacks have dependencies and must be deployed in this order:

```
1. BaseStack         (Foundation: IAM, Secrets, Parameters)
   ↓
2. NetworkStack      (Network: VPC - Optional, currently disabled)
   ↓
3. StorageStack      (Data: DynamoDB, S3)
   ↓
4. ComputeStack      (Compute: Lambda)
   ↓
5. FrontendStack     (Frontend: CloudFront, Static Website)
   ↓
6. MonitoringStack   (Observability: CloudWatch, Alarms)
```

CDK automatically handles these dependencies when you run `cdk deploy --all`.

## Individual Stack Deployment

If you need to deploy stacks individually:

```bash
# Deploy specific stack
cdk deploy BaseStack --context environment=dev

# Deploy multiple stacks in order
cdk deploy BaseStack StorageStack ComputeStack --context environment=dev
```

## Environment-Specific Deployment

### Development

```bash
cdk deploy --all --context environment=dev
```

### Staging

```bash
# Update cdk.json with staging account/region
cdk deploy --all --context environment=staging
```

### Production

```bash
# Update cdk.json with production account/region
# Review changes carefully!
cdk diff --all --context environment=prod

# Deploy with manual approval
cdk deploy --all --context environment=prod
```

## Updating Resources

### Update Lambda Function Code

```bash
# Make changes to lambda/reasoning-handler/index.py
# Deploy only ComputeStack
cdk deploy ComputeStack --context environment=dev
```

### Update Frontend Files

```bash
# Make changes to ../sample_calendar.html or other static files
# Deploy only FrontendStack
cdk deploy FrontendStack --context environment=dev

# Note: CloudFront invalidation may take 5-10 minutes
```

### Update Configuration

```bash
# Edit cdk.json environmentConfig

# Deploy affected stacks
cdk deploy --all --context environment=dev
```

### Update Bedrock Configuration

```bash
# Update Bedrock model in Parameter Store
aws ssm put-parameter \
    --name "/co2-analysis/dev/config/bedrock-model" \
    --value "amazon.nova-pro-v1:0" \
    --type String \
    --overwrite

# Lambda functions will use the new model on next invocation
```

## Monitoring Deployment

### CloudFormation Events

```bash
# Watch deployment progress
aws cloudformation describe-stack-events \
    --stack-name ComputeStack \
    --max-items 20
```

### Lambda Deployment

```bash
# Check Lambda function status
aws lambda get-function \
    --function-name co2-analysis-dev-reasoning-function \
    --query 'Configuration.[FunctionName,Runtime,State,LastUpdateStatus]'
```

### CloudFront Deployment

```bash
# Get distribution ID
DIST_ID=$(aws cloudformation describe-stacks \
    --stack-name FrontendStack \
    --query 'Stacks[0].Outputs[?OutputKey==`DistributionId`].OutputValue' \
    --output text)

# Check distribution status
aws cloudfront get-distribution \
    --id $DIST_ID \
    --query 'Distribution.Status'
# Status: "InProgress" or "Deployed"
```

## Rollback

### Rollback Single Stack

```bash
# Rollback to previous version
aws cloudformation rollback-stack --stack-name ComputeStack
```

### Complete Rollback

```bash
# Destroy all stacks (WARNING: Deletes all resources!)
cdk destroy --all --context environment=dev

# Then redeploy from known good version
git checkout <previous-commit>
cdk deploy --all --context environment=dev
```

## Cleanup

### Delete All Resources

```bash
# WARNING: This will delete all deployed resources!
cdk destroy --all --context environment=dev

# You will be prompted to confirm deletion of each stack
```

### Partial Cleanup

```bash
# Delete only specific stacks (order matters - reverse of deployment)
cdk destroy MonitoringStack --context environment=dev
cdk destroy FrontendStack --context environment=dev
cdk destroy ComputeStack --context environment=dev
# ... etc
```

## Troubleshooting Deployments

### Stack Fails to Deploy

1. Check CloudFormation events:
   ```bash
   aws cloudformation describe-stack-events \
       --stack-name STACK_NAME \
       --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`]'
   ```

2. Review error messages
3. Fix the issue in CDK code
4. Redeploy:
   ```bash
   cdk deploy STACK_NAME --context environment=dev
   ```

### Stack Stuck in UPDATE_ROLLBACK_FAILED

```bash
# Continue rollback
aws cloudformation continue-update-rollback --stack-name STACK_NAME

# If that fails, you may need to skip resources
aws cloudformation continue-update-rollback \
    --stack-name STACK_NAME \
    --resources-to-skip RESOURCE_LOGICAL_ID
```

### CloudFormation Drift Detection

```bash
# Detect drift
aws cloudformation detect-stack-drift --stack-name BaseStack

# Check drift status
aws cloudformation describe-stack-drift-detection-status \
    --stack-drift-detection-id <drift-detection-id>
```

## Cost Monitoring

### Set Up Billing Alerts

```bash
# Create SNS topic for billing alerts
aws sns create-topic --name billing-alerts

# Subscribe your email
aws sns subscribe \
    --topic-arn arn:aws:sns:us-east-1:ACCOUNT_ID:billing-alerts \
    --protocol email \
    --notification-endpoint your-email@example.com

# Create CloudWatch alarm for billing
aws cloudwatch put-metric-alarm \
    --alarm-name MonthlyBillingAlert \
    --alarm-description "Alert when monthly bill exceeds $50" \
    --metric-name EstimatedCharges \
    --namespace AWS/Billing \
    --statistic Maximum \
    --period 21600 \
    --evaluation-periods 1 \
    --threshold 50 \
    --comparison-operator GreaterThanThreshold \
    --alarm-actions arn:aws:sns:us-east-1:ACCOUNT_ID:billing-alerts
```

### View Current Costs

```bash
# AWS Cost Explorer (requires Cost Explorer to be enabled)
aws ce get-cost-and-usage \
    --time-period Start=2025-01-01,End=2025-02-01 \
    --granularity MONTHLY \
    --metrics UnblendedCost \
    --group-by Type=TAG,Key=Project
```

## Best Practices

### Before Deploying to Production

- [ ] Review all changes with `cdk diff`
- [ ] Test in dev/staging first
- [ ] Update alarm email addresses
- [ ] Enable X-Ray tracing
- [ ] Enable provisioned concurrency for Lambda
- [ ] Configure proper log retention
- [ ] Set up billing alerts
- [ ] Document any manual steps
- [ ] Create deployment runbook

### Regular Maintenance

- [ ] Review CloudWatch dashboards weekly
- [ ] Check for Lambda errors
- [ ] Monitor DynamoDB throttling
- [ ] Review costs monthly
- [ ] Update dependencies quarterly
- [ ] Rotate secrets annually

## Additional Resources

- [CDK README](./README.md) - Complete documentation
- [AWS CDK Workshop](https://cdkworkshop.com/)
- [CDK API Reference](https://docs.aws.amazon.com/cdk/api/v2/)
- [Project Specification](../specs/001-aws-cdk-migration/spec.md)

---

**Last Updated**: 2025-11-01
