# ComputeStack - Serverless Compute Layer

## Overview

The ComputeStack implements the serverless compute layer for the CO2 Anomaly Analysis System using AWS Lambda and API Gateway. This stack provides the reasoning API endpoint that generates AI-powered insights for CO2 concentration anomalies.

## Architecture

```
┌─────────────────┐
│  API Gateway    │ ← CORS, Validation, Throttling
│  /reasoning     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Lambda Function │ ← Python 3.11, 30s timeout
│ reasoning-api   │
└────────┬────────┘
         │
         ├───────────┐
         │           │
         ▼           ▼
┌──────────────┐  ┌────────────────┐
│  DynamoDB    │  │ Secrets Manager│
│  Cache Table │  │  Gemini API Key│
└──────────────┘  └────────────────┘
```

## Resources Created

### 1. Lambda Layer - Dependencies
- **Name**: `co2-analysis-{env}-reasoning-dependencies`
- **Runtime**: Python 3.11
- **Dependencies**:
  - google-generativeai==0.3.2
  - boto3==1.34.0
  - botocore==1.34.0

### 2. Lambda Function - Reasoning API
- **Name**: `co2-analysis-{env}-reasoning-api`
- **Runtime**: Python 3.11
- **Handler**: `index.lambda_handler`
- **Timeout**: 30 seconds
- **Memory**:
  - Dev: 256 MB
  - Prod: 512 MB
- **Concurrency**:
  - Dev: Unreserved
  - Prod: Reserved 100 concurrent executions
- **Provisioned Concurrency**: Configurable (default: 0 for dev, 1 for prod)

### 3. API Gateway REST API
- **Name**: `co2-analysis-{env}-reasoning-api`
- **Endpoint Type**: Regional
- **Stage**: `prod`
- **Endpoint**: `POST /reasoning`

#### Request Model
```json
{
  "lat": 35.6762,         // Required: Latitude (-90 to 90)
  "lon": 139.6503,        // Required: Longitude (-180 to 180)
  "co2": 420.5,           // Required: CO2 concentration in ppm
  "deviation": 5.0,       // Optional: Deviation from baseline
  "date": "2023-01-15",   // Optional: Observation date (YYYY-MM-DD)
  "severity": "high",     // Optional: low, medium, high
  "zscore": 2.5           // Optional: Statistical Z-score
}
```

#### Response Model
```json
{
  "reasoning": "AI-generated analysis text",
  "cached": false,
  "cache_key": "sha256_hash",
  "cached_at": "2023-01-15T10:30:00Z"  // Only if cached=true
}
```

## CORS Configuration

- **Allowed Origins**: `*` (All origins)
- **Allowed Methods**: `POST`, `OPTIONS`
- **Allowed Headers**: `Content-Type`, `X-Api-Key`, `Authorization`
- **Max Age**: 1 hour

## Throttling

Environment-specific throttling limits:

| Environment | Rate Limit | Burst Limit |
|-------------|------------|-------------|
| Dev         | 100 req/s  | 200         |
| Staging     | 500 req/s  | 1000        |
| Production  | 1000 req/s | 2000        |

## Request Validation

API Gateway validates:
- Required fields: `lat`, `lon`, `co2`
- Latitude range: -90 to 90
- Longitude range: -180 to 180
- CO2 minimum: 0
- Date pattern: YYYY-MM-DD (if provided)
- Severity enum: low, medium, high (if provided)

## Environment Variables

The Lambda function uses the following environment variables:

```bash
DYNAMODB_TABLE_NAME=co2-analysis-{env}-cache
GEMINI_API_KEY_SECRET_NAME=co2-analysis-{env}-gemini-api-key
CACHE_TTL_DAYS=90
GEMINI_MODEL=gemini-2.0-flash-exp
ENVIRONMENT=dev|staging|prod
LOG_LEVEL=DEBUG|INFO
```

## Parameter Store Exports

The stack exports the following parameters to AWS Systems Manager Parameter Store:

| Parameter Path | Description |
|----------------|-------------|
| `/co2-analysis/{env}/compute/api-gateway/url` | API Gateway endpoint URL |
| `/co2-analysis/{env}/compute/api-gateway/id` | API Gateway REST API ID |
| `/co2-analysis/{env}/compute/api-gateway/stage` | API Gateway stage name |
| `/co2-analysis/{env}/compute/lambda/function-arn` | Lambda function ARN |
| `/co2-analysis/{env}/compute/lambda/function-name` | Lambda function name |

## CloudFormation Outputs

| Output | Description | Export Name |
|--------|-------------|-------------|
| ApiUrl | API Gateway root URL | `co2-analysis-{env}-api-url` |
| ApiEndpoint | Full reasoning endpoint URL | `co2-analysis-{env}-reasoning-endpoint` |
| LambdaArn | Lambda function ARN | `co2-analysis-{env}-lambda-arn` |

## Dependencies

### Stack Dependencies

ComputeStack depends on:

1. **BaseStack** (Layer 1):
   - `lambdaExecutionRole` - IAM role for Lambda execution
   - `geminiApiKeySecret` - Secrets Manager secret for Gemini API key

2. **StorageStack** (Layer 3):
   - `cacheTable` - DynamoDB table for caching reasoning results

### IAM Permissions

The Lambda execution role (from BaseStack) requires:

1. **Basic Lambda Execution**:
   - CloudWatch Logs write permissions

2. **DynamoDB Access**:
   - `dynamodb:GetItem` - Read cached results
   - `dynamodb:PutItem` - Write new results

3. **Secrets Manager Access**:
   - `secretsmanager:GetSecretValue` - Read Gemini API key

4. **Parameter Store Access**:
   - `ssm:GetParameter` - Read configuration parameters

## Deployment

### Prerequisites

1. **AWS Account**: Configured AWS credentials
2. **Docker**: Required for building Lambda layer (see alternative methods below)
3. **Node.js**: v18+ with npm
4. **Dependencies**: `npm install` in cdk directory

### Standard Deployment (with Docker)

```bash
# Navigate to CDK directory
cd cdk

# Install dependencies
npm install

# Bootstrap CDK (first time only)
cdk bootstrap --context environment=dev

# Synthesize CloudFormation template
cdk synth ComputeStack --context environment=dev

# Deploy
cdk deploy ComputeStack --context environment=dev
```

### Deployment Without Docker

If Docker is not available, you have two options:

#### Option 1: Pre-build Lambda Layer

```bash
# Navigate to layer directory
cd cdk/lambda/layers/dependencies

# Install dependencies locally
pip install -r requirements.txt -t python/ --platform manylinux2014_x86_64 --only-binary=:all:

# Return to CDK directory
cd ../../..

# Deploy
cdk deploy ComputeStack --context environment=dev
```

#### Option 2: Use AWS Lambda Layers (Production)

For production deployments, consider using:
- AWS Lambda Layers for common packages
- Pre-built layers from AWS or community
- CI/CD pipeline with Docker for building layers

### Post-Deployment Configuration

After deployment, you MUST configure the Gemini API key:

```bash
# Get the secret ARN from stack outputs
SECRET_ARN=$(aws cloudformation describe-stacks \
  --stack-name BaseStack \
  --query 'Stacks[0].Outputs[?OutputKey==`GeminiApiKeySecretArn`].OutputValue' \
  --output text)

# Update the secret with your Gemini API key
aws secretsmanager update-secret \
  --secret-id $SECRET_ARN \
  --secret-string '{"apiKey":"YOUR_ACTUAL_GEMINI_API_KEY"}'
```

## Testing

### Test the API Endpoint

```bash
# Get the API endpoint
API_ENDPOINT=$(aws ssm get-parameter \
  --name "/co2-analysis/dev/compute/api-gateway/url" \
  --query 'Parameter.Value' \
  --output text)

# Test POST /reasoning
curl -X POST "${API_ENDPOINT}reasoning" \
  -H "Content-Type: application/json" \
  -d '{
    "lat": 35.6762,
    "lon": 139.6503,
    "co2": 420.5,
    "deviation": 5.0,
    "date": "2023-01-15",
    "severity": "high",
    "zscore": 2.5
  }'
```

Expected response:
```json
{
  "reasoning": "This CO₂ anomaly in Tokyo (35.68°N, 139.65°E) shows a concentration of 420.5 ppm, which is 5 ppm above baseline. Given the high severity and Z-score of 2.5, this is likely due to...",
  "cached": false,
  "cache_key": "abc123..."
}
```

### Test Caching

Make the same request twice - the second request should return `"cached": true` and respond faster.

### Test Validation

```bash
# Missing required field (should return 400)
curl -X POST "${API_ENDPOINT}reasoning" \
  -H "Content-Type: application/json" \
  -d '{"lat": 35.6762, "co2": 420.5}'

# Invalid latitude (should return 400)
curl -X POST "${API_ENDPOINT}reasoning" \
  -H "Content-Type: application/json" \
  -d '{"lat": 95, "lon": 139.6503, "co2": 420.5}'
```

## Monitoring

### CloudWatch Logs

Lambda logs are available at:
```
/aws/lambda/co2-analysis-{env}-reasoning-api
```

Log retention: 7 days

### CloudWatch Metrics

Key metrics to monitor:
- `Invocations` - Number of Lambda invocations
- `Duration` - Execution time
- `Errors` - Failed invocations
- `Throttles` - Throttled requests
- `ConcurrentExecutions` - Concurrent executions

API Gateway metrics:
- `Count` - Number of API requests
- `4XXError` - Client errors
- `5XXError` - Server errors
- `Latency` - End-to-end latency

### X-Ray Tracing

X-Ray is enabled for staging and production environments. View traces in the AWS X-Ray console.

## Cost Optimization

### Development
- Provisioned concurrency: Disabled (cold starts acceptable)
- Memory: 256 MB (lower cost)
- Log retention: 7 days

### Production
- Provisioned concurrency: 1 (reduced cold starts)
- Memory: 512 MB (faster execution, potentially lower cost)
- Reserved concurrency: 100 (prevent runaway costs)

### Caching Strategy

The DynamoDB cache reduces Gemini API costs:
- Cache hit: ~$0.00025 (DynamoDB read)
- Cache miss: ~$0.015 (Gemini API call + DynamoDB write)
- 90-day TTL reduces storage costs

## Security

### CDK Nag Suppressions

The following security rules are suppressed with justifications:

1. **AwsSolutions-APIG4** (API Gateway Authorization):
   - Reason: Public API by design
   - Mitigation: Rate limiting, WAF in production

2. **AwsSolutions-APIG1** (Access Logging) - Dev only:
   - Reason: Cost optimization for development
   - Mitigation: Enabled in staging/production

3. **AwsSolutions-APIG6** (X-Ray Tracing) - Dev only:
   - Reason: Cost optimization for development
   - Mitigation: Enabled in staging/production

4. **AwsSolutions-L3** (DLQ):
   - Reason: Synchronous invocation, errors returned to client
   - Mitigation: Comprehensive CloudWatch logging

### Best Practices

1. **Least Privilege IAM**: Lambda role has minimal required permissions
2. **Secrets Management**: API keys in Secrets Manager (not environment variables)
3. **Input Validation**: API Gateway validates all inputs
4. **Rate Limiting**: Environment-specific throttling
5. **Monitoring**: CloudWatch logs and metrics
6. **Encryption**: All data encrypted at rest and in transit

## Troubleshooting

### Lambda Function Errors

**Error**: "Failed to retrieve API key from Secrets Manager"
- **Solution**: Ensure Gemini API key is configured in Secrets Manager

**Error**: "Gemini API error"
- **Solution**: Check API key validity and Gemini API quota

**Error**: "Error retrieving from cache"
- **Solution**: Verify DynamoDB table exists and Lambda has permissions

### API Gateway Errors

**Error**: 400 Bad Request
- **Solution**: Check request body matches schema

**Error**: 429 Too Many Requests
- **Solution**: Reduce request rate or increase throttling limits

**Error**: 500 Internal Server Error
- **Solution**: Check CloudWatch logs for Lambda errors

### Build Errors

**Error**: "spawnSync docker ENOENT"
- **Solution**: Install Docker or use manual layer build

**Error**: "Cannot find module '../lib/base-stack'"
- **Solution**: Ensure all stack files exist or create stubs

## Future Enhancements

Potential improvements for future iterations:

1. **API Authentication**: Add API key or Cognito authorization
2. **WAF Integration**: AWS WAF for additional security
3. **API Versioning**: Support multiple API versions
4. **Batch Processing**: Batch endpoint for multiple locations
5. **Async Processing**: SQS queue for long-running requests
6. **Enhanced Caching**: Redis/ElastiCache for frequently accessed data
7. **Multi-Region**: Deploy in multiple regions for lower latency
8. **Custom Domain**: Use custom domain with SSL certificate

## Support

For issues or questions:
1. Check CloudWatch logs
2. Review AWS CloudFormation events
3. Consult CDK documentation
4. Review GitHub issues

## License

This stack is part of the CO2 Anomaly Analysis System project.
