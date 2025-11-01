# CO₂ Anomaly Analysis System - AWS CDK Infrastructure

This directory contains the AWS CDK infrastructure code for deploying the CO₂ Anomaly Analysis System to AWS using a serverless architecture.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Stack Structure](#stack-structure)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Deployment](#deployment)
- [Configuration](#configuration)
- [Development](#development)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Cost Estimation](#cost-estimation)

## Overview

This CDK application deploys a complete serverless infrastructure for the CO₂ Anomaly Analysis System, migrating from the Phase 1 local Flask prototype to a production-ready AWS environment.

### Key Features

- **Serverless Architecture**: Lambda, API Gateway, DynamoDB, S3, CloudFront
- **Infrastructure as Code**: Full AWS CDK TypeScript implementation
- **Multi-Environment Support**: Dev, Staging, and Production configurations
- **Security Best Practices**: IAM roles, Secrets Manager, encryption at rest/transit
- **Monitoring & Alerting**: CloudWatch dashboards, alarms, SNS notifications
- **Cost Optimized**: Pay-per-use model with prototype-level defaults

### Technology Stack

| Component | Service | Purpose |
|-----------|---------|---------|
| **IaC** | AWS CDK (TypeScript) | Infrastructure as Code |
| **Compute** | AWS Lambda (Python 3.11) | Serverless functions |
| **API** | API Gateway | HTTP API endpoints |
| **Storage** | DynamoDB + S3 | Cache + data files |
| **CDN** | CloudFront | Content delivery |
| **Security** | Secrets Manager + IAM | API keys + access control |
| **Monitoring** | CloudWatch + X-Ray + SNS | Logs, metrics, tracing, alerts |
| **AI** | Google Gemini API | Reasoning generation |

## Architecture

### High-Level Architecture

```
Browser
    ↓
CloudFront (CDN)
    ↓
┌──────────────────┬─────────────────┐
│   Static Files   │   API Gateway   │
│   (S3)           │   (REST API)    │
└──────────────────┴─────────────────┘
                          ↓
                    Lambda Function
                          ↓
        ┌─────────────────┼─────────────────┐
        ↓                 ↓                 ↓
   DynamoDB          Secrets Mgr      Gemini API
   (Cache)           (API Key)        (External)
```

### Stack Dependency Graph

```
Layer 1: BaseStack (Foundation)
            ↓
Layer 2: NetworkStack (Network - Optional)
            ↓
Layer 3: StorageStack (Data)
            ↓
Layer 4: ComputeStack (Compute)
            ↓
    ┌───────┴───────┐
    ↓               ↓
Layer 5:      Layer 6:
FrontendStack  MonitoringStack
```

## Stack Structure

### 1. BaseStack (Foundation Layer)

**Purpose**: Shared resources used by all other stacks

**Resources**:
- IAM execution role for Lambda functions
- Secrets Manager secret for Gemini API key
- SSM parameters for configuration (model, TTL, timeouts)

**Dependencies**: None

**File**: `lib/base-stack.ts`

---

### 2. NetworkStack (Network Layer)

**Purpose**: Networking resources (optional for current prototype)

**Resources**:
- VPC with public/private subnets (commented out)
- Security groups for Lambda (commented out)
- VPC endpoints for cost optimization (commented out)

**Dependencies**: BaseStack

**File**: `lib/network-stack.ts`

**Note**: VPC is not required for the current prototype. Lambda functions run without VPC. Uncomment VPC configuration if needed for future enhancements (e.g., RDS, ElastiCache).

---

### 3. StorageStack (Data Layer)

**Purpose**: Data storage for cache and static files

**Resources**:
- **DynamoDB Table**: Cache for AI reasoning results
  - Partition key: `cache_key` (SHA256 hash)
  - TTL enabled (90 days default)
  - On-demand billing mode
  - Global Secondary Index on `cached_at`
- **S3 Bucket (GeoJSON)**: CO₂ anomaly data files
  - CORS enabled
  - Versioning disabled
- **S3 Bucket (Static Website)**: HTML, CSS, JS files
  - CloudFront OAI access only
  - Versioning enabled in production

**Dependencies**: BaseStack

**File**: `lib/storage-stack.ts`

---

### 4. ComputeStack (Compute Layer)

**Purpose**: Serverless compute for API logic

**Resources**:
- **Lambda Function**: Reasoning API handler
  - Runtime: Python 3.11
  - Handler: `index.lambda_handler`
  - Timeout: 30 seconds
  - Memory: 256 MB (dev), 512 MB (prod)
  - Environment variables: DynamoDB table, secret name, model config
  - X-Ray tracing (optional)
  - Provisioned concurrency in production (reduces cold starts)
- **Lambda Layer**: Python dependencies
  - `google-generativeai`
  - `boto3`
  - Bundled during deployment

**Dependencies**: BaseStack, StorageStack

**File**: `lib/compute-stack.ts`

---

### 5. FrontendStack (Frontend Layer)

**Purpose**: Static website hosting and CDN

**Resources**:
- **CloudFront Distribution**:
  - Default behavior: S3 static website
  - `/data/geojson/*`: GeoJSON S3 bucket
  - `/api/*`: API Gateway (when implemented)
  - Custom cache policies for each origin
  - Error responses (404/403 → index.html)
  - HTTPS only
- **Origin Access Identity (OAI)**: CloudFront → S3 access
- **S3 Bucket Deployment**: Automated upload of static files

**Dependencies**: StorageStack

**File**: `lib/frontend-stack.ts`

---

### 6. MonitoringStack (Observability Layer)

**Purpose**: Monitoring, logging, and alerting

**Resources**:
- **CloudWatch Dashboard**: Visual metrics for all components
- **CloudWatch Alarms**:
  - Lambda errors (> 5 in 5 min)
  - Lambda duration (> 25s, approaching 30s timeout)
  - Lambda throttles (≥ 1)
  - DynamoDB throttles (> 10 in 5 min)
  - API Gateway 5xx errors (> 10 in 5 min)
  - API Gateway latency (> 10s average)
- **SNS Topic**: Email notifications for alarms

**Dependencies**: ComputeStack, StorageStack

**File**: `lib/monitoring-stack.ts`

---

## Prerequisites

### Required Tools

1. **Node.js** (v18 or later)
   ```bash
   node --version  # Should be >= 18.0.0
   ```

2. **AWS CLI** (v2)
   ```bash
   aws --version
   aws configure  # Set up credentials
   ```

3. **AWS CDK CLI** (v2)
   ```bash
   npm install -g aws-cdk
   cdk --version  # Should be >= 2.133.0
   ```

4. **TypeScript**
   ```bash
   npm install -g typescript
   tsc --version
   ```

### AWS Account Setup

1. **AWS Account**: You need an AWS account with appropriate permissions
2. **IAM Permissions**: Your IAM user/role needs permissions to create:
   - CloudFormation stacks
   - Lambda functions
   - DynamoDB tables
   - S3 buckets
   - CloudFront distributions
   - IAM roles and policies
   - Secrets Manager secrets
   - CloudWatch resources

3. **AWS Credentials**: Configure AWS credentials
   ```bash
   aws configure
   # Enter: Access Key ID, Secret Access Key, Region, Output format
   ```

## Getting Started

### 1. Install Dependencies

```bash
cd cdk
npm install
```

This installs:
- `aws-cdk-lib` - AWS CDK core library
- `constructs` - CDK constructs
- TypeScript and development tools

### 2. Bootstrap CDK (First Time Only)

Bootstrap creates the necessary AWS resources for CDK deployments in your account/region:

```bash
cdk bootstrap aws://ACCOUNT-NUMBER/REGION

# Example:
cdk bootstrap aws://123456789012/us-east-1
```

**What bootstrapping does**:
- Creates an S3 bucket for CDK assets (Lambda code, CloudFormation templates)
- Creates IAM roles for CloudFormation deployments
- Only needs to be done once per account/region

### 3. Configure Environment

Edit `cdk.json` and update the `environmentConfig` section:

```json
{
  "environmentConfig": {
    "dev": {
      "account": "123456789012",        // ← Your AWS account ID
      "region": "us-east-1",             // ← Your preferred region
      "alarmEmail": "you@example.com",   // ← Your email for alerts
      ...
    }
  }
}
```

### 4. Store Gemini API Key

Before deploying, store your Gemini API key in Secrets Manager:

```bash
# Option 1: AWS Console
# Go to Secrets Manager → Store a new secret → Other type of secret
# Key: GEMINI_API_KEY, Value: your-api-key-here
# Secret name: co2-analysis-dev-gemini-api-key

# Option 2: AWS CLI
aws secretsmanager create-secret \
    --name co2-analysis-dev-gemini-api-key \
    --description "Google Gemini API Key for CO2 Analysis" \
    --secret-string '{"GEMINI_API_KEY":"your-api-key-here"}'
```

**Note**: The BaseStack creates the secret placeholder. You need to update it with your actual API key after deployment.

## Deployment

### Development Environment

Deploy all stacks to the development environment:

```bash
# Synthesize CloudFormation templates (preview)
cdk synth --context environment=dev

# Preview changes
cdk diff --all --context environment=dev

# Deploy all stacks
cdk deploy --all --context environment=dev

# Deploy with auto-approval (skip confirmations)
cdk deploy --all --context environment=dev --require-approval never
```

### Deploy Individual Stacks

```bash
# Deploy only BaseStack
cdk deploy BaseStack --context environment=dev

# Deploy stacks in order
cdk deploy BaseStack NetworkStack StorageStack --context environment=dev
```

### Staging/Production Deployment

```bash
# Staging
cdk deploy --all --context environment=staging

# Production
cdk deploy --all --context environment=prod
```

### Post-Deployment Steps

1. **Update Gemini API Key Secret**:
   ```bash
   aws secretsmanager update-secret \
       --secret-id co2-analysis-dev-gemini-api-key \
       --secret-string '{"GEMINI_API_KEY":"your-actual-api-key"}'
   ```

2. **Upload GeoJSON Files to S3**:
   ```bash
   # Get bucket name from CloudFormation outputs
   aws cloudformation describe-stacks \
       --stack-name StorageStack \
       --query 'Stacks[0].Outputs[?OutputKey==`GeoJsonBucketName`].OutputValue' \
       --output text

   # Upload files
   aws s3 cp ../data/geojson/ s3://BUCKET-NAME/data/geojson/ --recursive
   ```

3. **Get CloudFront URL**:
   ```bash
   aws cloudformation describe-stacks \
       --stack-name FrontendStack \
       --query 'Stacks[0].Outputs[?OutputKey==`WebsiteUrl`].OutputValue' \
       --output text
   ```

4. **Subscribe to SNS Alarms** (if email not auto-confirmed):
   - Check your email for SNS subscription confirmation
   - Click "Confirm subscription"

## Configuration

### Environment Variables (cdk.json)

Each environment (dev, staging, prod) has its own configuration:

```json
{
  "account": "",              // AWS account ID
  "region": "us-east-1",      // AWS region
  "environment": "dev",       // Environment name
  "projectName": "co2-analysis",
  "appName": "CO2 Anomaly Analysis",
  "provisionedConcurrency": 0,  // Lambda provisioned concurrency (0 = disabled)
  "wafEnabled": false,          // Enable WAF (future)
  "enableXRay": false,          // Enable X-Ray tracing
  "logRetentionDays": 7,        // CloudWatch Logs retention
  "alarmEmail": "",             // Email for SNS alarms
  "cacheTtlDays": 90,           // DynamoDB cache TTL
  "apiThrottling": {
    "rateLimit": 100,           // Requests per second
    "burstLimit": 200           // Burst capacity
  }
}
```

### Naming Convention

All resources follow this naming pattern:

```
{projectName}-{environment}-{resourceName}

Examples:
- co2-analysis-dev-lambda-execution-role
- co2-analysis-prod-cache (DynamoDB table)
- co2-analysis-staging-static-website (S3 bucket)
```

### Tagging Strategy

All resources are automatically tagged with:

```yaml
Project: co2-analysis
Environment: dev | staging | prod
Application: CO2 Anomaly Analysis
ManagedBy: CDK
CreatedBy: AWS-CDK
Layer: 1-Foundation | 2-Network | 3-Data | 4-Compute | 5-Frontend | 6-Observability
```

## Development

### Project Structure

```
cdk/
├── bin/
│   └── co2-analysis-app.ts       # CDK app entry point
├── lib/
│   ├── base-stack.ts             # IAM, Secrets, SSM
│   ├── network-stack.ts          # VPC, Security Groups (optional)
│   ├── storage-stack.ts          # DynamoDB, S3
│   ├── compute-stack.ts          # Lambda, Layer
│   ├── frontend-stack.ts         # CloudFront, S3 static hosting
│   └── monitoring-stack.ts       # CloudWatch, SNS
├── lambda/
│   ├── reasoning-handler/
│   │   ├── index.py              # Lambda handler
│   │   └── requirements.txt
│   └── layers/
│       └── dependencies/
│           └── requirements.txt  # Layer dependencies
├── config/
│   └── environment.ts            # Environment configuration utilities
├── test/
│   └── *.test.ts                 # CDK tests (TODO)
├── cdk.json                      # CDK configuration
├── package.json                  # Node.js dependencies
├── tsconfig.json                 # TypeScript configuration
└── README.md                     # This file
```

### Adding a New Stack

1. Create stack file in `lib/`:
   ```typescript
   // lib/new-stack.ts
   import * as cdk from 'aws-cdk-lib';
   import { Construct } from 'constructs';
   import { EnvironmentConfig, getResourceName, getResourceTags } from '../config/environment';

   export class NewStack extends cdk.Stack {
     constructor(scope: Construct, id: string, config: EnvironmentConfig, props?: cdk.StackProps) {
       super(scope, id, props);

       // Apply tags
       const tags = getResourceTags(config);
       Object.entries(tags).forEach(([key, value]) => {
         cdk.Tags.of(this).add(key, value);
       });

       // Add resources...
     }
   }
   ```

2. Import in `bin/co2-analysis-app.ts`:
   ```typescript
   import { NewStack } from '../lib/new-stack';

   const newStack = new NewStack(app, 'NewStack', config, { env });
   newStack.addDependency(baseStack); // Add dependencies
   ```

### Useful Commands

```bash
# Build TypeScript
npm run build

# Watch mode (auto-compile on changes)
npm run watch

# Synthesize CloudFormation templates
npm run cdk:synth

# Show difference between deployed and current code
npm run cdk:diff

# Deploy all stacks
npm run cdk:deploy

# Deploy specific stack
npm run cdk:deploy:base      # BaseStack
npm run cdk:deploy:storage   # StorageStack
npm run cdk:deploy:compute   # ComputeStack
npm run cdk:deploy:frontend  # FrontendStack
npm run cdk:deploy:monitoring # MonitoringStack

# Destroy all stacks (WARNING: Deletes resources!)
npm run cdk:destroy

# Run tests
npm test

# Lint TypeScript code
npm run lint

# Format code
npm run format
```

## Testing

### CDK Tests (TODO)

Unit tests for CDK stacks using Jest:

```bash
npm test
```

Example test structure:

```typescript
// test/base-stack.test.ts
import * as cdk from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';
import { BaseStack } from '../lib/base-stack';

test('BaseStack creates Lambda execution role', () => {
  const app = new cdk.App();
  const config = { /* test config */ };

  const stack = new BaseStack(app, 'TestStack', config);
  const template = Template.fromStack(stack);

  template.hasResourceProperties('AWS::IAM::Role', {
    AssumeRolePolicyDocument: {
      Statement: [{
        Action: 'sts:AssumeRole',
        Effect: 'Allow',
        Principal: {
          Service: 'lambda.amazonaws.com'
        }
      }]
    }
  });
});
```

### Integration Testing

Test deployed stacks:

```bash
# Test Lambda function directly
aws lambda invoke \
    --function-name co2-analysis-dev-reasoning-function \
    --payload '{"body": "{\"lat\": 35.6762, \"lon\": 139.6503, \"co2\": 420.5, \"deviation\": 5.0, \"date\": \"2023-01-15\", \"severity\": \"high\", \"zscore\": 2.5}"}' \
    response.json

cat response.json

# Test DynamoDB cache
aws dynamodb scan \
    --table-name co2-analysis-dev-cache \
    --limit 5

# Test S3 bucket
aws s3 ls s3://co2-analysis-dev-geojson-data/data/geojson/
```

## Troubleshooting

### Common Issues

#### 1. CDK Bootstrap Error

**Error**: `Need to perform AWS calls for account XXX, but no credentials configured`

**Solution**:
```bash
aws configure
# Enter your AWS credentials

# Then bootstrap
cdk bootstrap
```

#### 2. Stack Deployment Fails

**Error**: `Resource handler returned message: "User: ... is not authorized to perform: ..."`

**Solution**: Your IAM user/role needs additional permissions. Attach policies:
- `PowerUserAccess` (recommended for dev)
- Or create custom policy with required permissions

#### 3. Lambda Function Timeout

**Error**: Lambda function times out after 30 seconds

**Solution**:
- Check Gemini API response time
- Increase Lambda timeout in `compute-stack.ts` (max 900 seconds)
- Enable provisioned concurrency to reduce cold starts

#### 4. DynamoDB Throttling

**Error**: `ProvisionedThroughputExceededException`

**Solution**:
- Billing mode is already on-demand (auto-scales)
- Check for excessive requests
- Implement exponential backoff in Lambda

#### 5. CloudFront Distribution Takes Long to Deploy

**Issue**: CloudFront deployment takes 15-20 minutes

**Solution**: This is normal. CloudFront distributions propagate globally.

```bash
# Check deployment status
aws cloudfront get-distribution \
    --id DISTRIBUTION_ID \
    --query 'Distribution.Status'
```

#### 6. Secret Not Found Error

**Error**: `ResourceNotFoundException: Secrets Manager can't find the specified secret`

**Solution**: Update the secret with your Gemini API key after BaseStack deployment:

```bash
aws secretsmanager update-secret \
    --secret-id co2-analysis-dev-gemini-api-key \
    --secret-string '{"GEMINI_API_KEY":"your-key-here"}'
```

### Debugging

#### View CloudFormation Events

```bash
# List stacks
aws cloudformation list-stacks

# Describe stack events
aws cloudformation describe-stack-events \
    --stack-name BaseStack \
    --max-items 20
```

#### View Lambda Logs

```bash
# Get log streams
aws logs describe-log-streams \
    --log-group-name /aws/lambda/co2-analysis-dev-reasoning-function \
    --order-by LastEventTime \
    --descending \
    --max-items 5

# Get recent logs
aws logs tail /aws/lambda/co2-analysis-dev-reasoning-function --follow
```

#### View DynamoDB Items

```bash
aws dynamodb scan \
    --table-name co2-analysis-dev-cache \
    --limit 10
```

## Cost Estimation

### Monthly Cost Breakdown (Prototype - Moderate Usage)

Assumptions:
- 10,000 API requests/month
- 50% cache hit rate
- Average Lambda execution: 3 seconds
- Data transfer: 10 GB/month

| Service | Usage | Cost |
|---------|-------|------|
| **Lambda** | 5,000 invocations × 3s × 256MB | $0.20 |
| **DynamoDB** | 10,000 reads, 5,000 writes | $1.25 |
| **S3** | 10 GB storage + requests | $0.50 |
| **CloudFront** | 10 GB data transfer | $1.00 |
| **API Gateway** | 10,000 requests | $0.35 |
| **Secrets Manager** | 1 secret | $0.40 |
| **CloudWatch** | Logs + metrics | $5.00 |
| **Data Transfer** | Outbound | $0.90 |
| **Total** | | **~$9.60/month** |

**Cost optimization tips**:
- Enable CloudFront caching (reduces Lambda invocations)
- Use DynamoDB on-demand billing (current default)
- Set CloudWatch Logs retention to 7 days (dev) or 30 days (prod)
- Delete old CloudFront logs with S3 lifecycle policies

### Production Cost Estimate

For production with 100,000 requests/month:
- **Estimated cost**: $50-100/month
- Main cost drivers: Lambda invocations, CloudFront data transfer, CloudWatch Logs

## Security

### CDK Nag Integration

This project uses **CDK Nag** to enforce AWS security best practices automatically during synthesis. All stacks are validated against AWS Solutions best practices.

#### Running Security Checks

```bash
# Security checks run automatically during synthesis
npm run build
npx cdk synth --context environment=dev

# ✅ No errors = all security checks passed
# ⚠️  Warnings = review recommended (all documented)
# ❌ Errors = must be fixed before deployment
```

#### Security Best Practices Implemented

✅ **S3 Security**
- All buckets block public access
- Encryption at rest (AES-256)
- TLS/HTTPS enforced for all operations
- Access logging enabled
- CloudFront OAI for bucket access

✅ **IAM Security**
- Least-privilege IAM roles
- No wildcard permissions (except documented exceptions)
- Service-specific principals only

✅ **Data Protection**
- Secrets Manager for API keys (encrypted at rest)
- DynamoDB encryption at rest
- All data in transit uses TLS/HTTPS
- Point-in-time recovery (production only)

✅ **CloudFront Security**
- HTTPS-only connections
- Security headers (HSTS, X-Content-Type-Options, X-Frame-Options)
- Access logging enabled
- TLS 1.2 minimum protocol version

✅ **Monitoring**
- CloudWatch Logs with retention policies
- CloudWatch Alarms for security events
- SNS notifications with TLS enforcement

#### Security Documentation

For detailed security information, see:
- **[SECURITY.md](./SECURITY.md)** - Complete security documentation
  - CDK Nag suppressions with justifications
  - Security controls for each stack
  - Compliance and audit information
  - Security recommendations

#### Security Suppressions

All CDK Nag suppressions are documented with proper justifications. To validate suppressions:

```bash
# All suppressions have been validated with CheckCDKNagSuppressions tool
# Review SECURITY.md for complete suppression documentation
```

**Summary of Suppressions:**
- AwsSolutions-SMG4: Third-party API key (manual rotation)
- AwsSolutions-IAM4: AWS managed policies (best practices)
- AwsSolutions-IAM5: DynamoDB GSI wildcard (required)
- AwsSolutions-DDB3: PITR disabled for dev (cost optimization)
- AwsSolutions-CFR1: Global scientific data access
- AwsSolutions-CFR2: WAF enabled for prod/staging only
- AwsSolutions-CFR4: Default CloudFront certificate

All suppressions are documented with evidence and justification in [SECURITY.md](./SECURITY.md).

## Additional Resources

- [SECURITY.md](./SECURITY.md) - Security best practices and CDK Nag documentation
- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [CloudFront Documentation](https://docs.aws.amazon.com/cloudfront/)
- [AWS Security Best Practices](https://docs.aws.amazon.com/security/)
- [CDK Nag Documentation](https://github.com/cdklabs/cdk-nag)
- [Project Specification](../specs/001-aws-cdk-migration/spec.md)
- [Phase 2 Architecture Diagram](../specs/001-aws-cdk-migration/diagrams/phase2-architecture.md)

## Support

For issues and questions:
1. Check [Troubleshooting](#troubleshooting) section
2. Review AWS CloudWatch Logs
3. Check AWS CloudFormation stack events
4. Consult project documentation in `specs/001-aws-cdk-migration/`

---

**Next Steps**: After deploying the CDK stacks, proceed to [Phase 4: API Layer](../specs/001-aws-cdk-migration/spec.md#phase-4-api-layer-week-2-3) to implement API Gateway with authentication.
