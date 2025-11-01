# Parameter Store Integration Documentation

## Overview

This document describes the Parameter Store integration implemented across all CDK stacks to enable secure configuration sharing and cross-stack communication.

## Implementation Summary

All CDK stacks now export their critical resource identifiers to AWS Systems Manager (SSM) Parameter Store, enabling:
- Secure cross-stack resource sharing
- Runtime configuration discovery
- External system integration
- Centralized configuration management

## Parameter Store Naming Convention

All parameters follow a hierarchical naming structure:

```
/{projectName}/{environment}/{stack}/{resource-type}/{parameter-name}

Examples:
/co2-analysis/dev/storage/dynamodb/cache-table-name
/co2-analysis/dev/storage/dynamodb/cache-table-arn
/co2-analysis/dev/compute/api-gateway/url
/co2-analysis/dev/frontend/cloudfront/distribution-url
```

### Naming Components:
- **projectName**: `co2-analysis` (from config)
- **environment**: `dev`, `staging`, or `prod`
- **stack**: `base`, `storage`, `compute`, `frontend`, `monitoring`, `network`
- **resource-type**: `dynamodb`, `s3`, `api-gateway`, `lambda`, `cloudfront`, etc.
- **parameter-name**: Descriptive identifier

## Stack-by-Stack Integration

### 1. BaseStack (Layer 1 - Foundation)

**Purpose**: Provides IAM roles, secrets, and foundational configuration.

**Parameters Exported:**

| Parameter Path | Description | Value Type |
|---------------|-------------|------------|
| `/co2-analysis/{env}/config/gemini-model` | Gemini AI model identifier | String |
| `/co2-analysis/{env}/config/cache-ttl-days` | Cache TTL in days | String (number) |
| `/co2-analysis/{env}/config/function-timeout-seconds` | Lambda timeout | String (number) |

**Key Resources:**
- Lambda Execution Role (exported via props)
- Gemini API Key Secret (Secrets Manager)

**File**: `cdk/lib/base-stack.ts:80-104`

### 2. StorageStack (Layer 3 - Data)

**Purpose**: Manages DynamoDB tables and S3 buckets for data storage.

**Parameters Exported:**

| Parameter Path | Description | Value Type |
|---------------|-------------|------------|
| `/co2-analysis/{env}/storage/dynamodb/cache-table-name` | DynamoDB cache table name | String |
| `/co2-analysis/{env}/storage/dynamodb/cache-table-arn` | DynamoDB cache table ARN | ARN |
| `/co2-analysis/{env}/storage/s3/geojson-bucket-name` | GeoJSON S3 bucket name | String |
| `/co2-analysis/{env}/storage/s3/geojson-bucket-arn` | GeoJSON S3 bucket ARN | ARN |
| `/co2-analysis/{env}/storage/s3/website-bucket-name` | Static website S3 bucket name | String |
| `/co2-analysis/{env}/storage/s3/website-bucket-arn` | Static website S3 bucket ARN | ARN |

**Key Resources:**
- DynamoDB Cache Table
- S3 GeoJSON Bucket
- S3 Static Website Bucket

**File**: `cdk/lib/storage-stack.ts:105-164`

### 3. ComputeStack (Layer 4 - Compute)

**Purpose**: Lambda function and API Gateway for compute operations.

**Parameters Exported:**

| Parameter Path | Description | Value Type |
|---------------|-------------|------------|
| `/co2-analysis/{env}/compute/api-gateway/url` | API Gateway endpoint URL | URL |
| `/co2-analysis/{env}/compute/api-gateway/id` | API Gateway REST API ID | String |
| `/co2-analysis/{env}/compute/api-gateway/stage` | API Gateway stage name | String |
| `/co2-analysis/{env}/compute/lambda/function-arn` | Lambda function ARN | ARN |
| `/co2-analysis/{env}/compute/lambda/function-name` | Lambda function name | String |

**Parameters Imported:**

| Parameter Path | Usage |
|---------------|-------|
| `/co2-analysis/{env}/storage/dynamodb/cache-table-name` | Read DynamoDB table name (via lookup) |

**Cross-Stack Dependencies:**
- Receives DynamoDB table reference via props from StorageStack
- Receives Lambda execution role via props from BaseStack
- Receives Gemini API key secret via props from BaseStack

**File**: `cdk/lib/compute-stack.ts:25-37, 146-177`

### 4. FrontendStack (Layer 5 - Frontend)

**Purpose**: CloudFront distribution and static website hosting.

**Parameters Exported:**

| Parameter Path | Description | Value Type |
|---------------|-------------|------------|
| `/co2-analysis/{env}/frontend/cloudfront/distribution-url` | CloudFront HTTPS URL | URL |
| `/co2-analysis/{env}/frontend/cloudfront/distribution-domain` | CloudFront domain name | String |
| `/co2-analysis/{env}/frontend/cloudfront/distribution-id` | CloudFront distribution ID | String |
| `/co2-analysis/{env}/frontend/s3/website-bucket-name` | Static website bucket name | String |

**Parameters Imported:**

| Parameter Path | Usage |
|---------------|-------|
| `/co2-analysis/{env}/compute/api-gateway/url` | Configure API origin in CloudFront |

**Cross-Stack Dependencies:**
- Receives S3 buckets via props from StorageStack

**File**: `cdk/lib/frontend-stack.ts:24-31, 127-159`

### 5. MonitoringStack (Layer 6 - Observability)

**Purpose**: CloudWatch dashboards, alarms, and SNS notifications.

**Parameters Exported:**

| Parameter Path | Description | Value Type |
|---------------|-------------|------------|
| `/co2-analysis/{env}/monitoring/sns/alarm-topic-arn` | SNS alarm topic ARN | ARN |
| `/co2-analysis/{env}/monitoring/cloudwatch/dashboard-name` | CloudWatch dashboard name | String |

**Cross-Stack Dependencies:**
- Receives Lambda function reference via props from ComputeStack
- Receives DynamoDB table reference via props from StorageStack

**File**: `cdk/lib/monitoring-stack.ts:181-195`

### 6. NetworkStack (Layer 2 - Network) [Optional]

**Purpose**: VPC and security groups (currently disabled to reduce costs).

**Status**: VPC code is commented out. Uncomment when needed.

**File**: `cdk/lib/network-stack.ts`

## Cross-Stack Communication Patterns

### Pattern 1: Direct Props Passing (Compile-Time)

Used for tight coupling between stacks during synthesis:

```typescript
// In co2-analysis-app.ts
const storageStack = new StorageStack(app, 'StorageStack', config, {
  lambdaExecutionRole: baseStack.lambdaExecutionRole,
});

const computeStack = new ComputeStack(app, 'ComputeStack', config, {
  cacheTable: storageStack.cacheTable,
  lambdaExecutionRole: baseStack.lambdaExecutionRole,
});
```

**Advantages:**
- Type-safe references
- CDK automatically manages dependencies
- Compile-time validation

### Pattern 2: Parameter Store Lookup (Runtime)

Used for runtime configuration and external integrations:

```typescript
// Reading from Parameter Store
const apiUrl = ssm.StringParameter.valueFromLookup(
  this,
  '/co2-analysis/dev/compute/api-gateway/url'
);
```

**Advantages:**
- Enables runtime discovery
- Allows external systems to access configuration
- Supports independent stack deployments

### Pattern 3: CloudFormation Exports

Traditional CDK cross-stack exports (also implemented):

```typescript
new cdk.CfnOutput(this, 'ApiUrl', {
  value: this.api.url,
  exportName: `${config.projectName}-${config.environment}-api-url`,
});
```

## Security Considerations

### IAM Permissions

The Lambda Execution Role in BaseStack has permissions to read Parameter Store:

```typescript
this.lambdaExecutionRole.addToPolicy(
  new iam.PolicyStatement({
    effect: iam.Effect.ALLOW,
    actions: [
      'ssm:GetParameter',
      'ssm:GetParameters',
      'ssm:GetParametersByPath',
    ],
    resources: [
      `arn:aws:ssm:${this.region}:${this.account}:parameter/${config.projectName}/${config.environment}/*`,
    ],
  })
);
```

**Scope**: Limited to project-specific parameters only.

### Parameter Tier

All parameters use `ssm.ParameterTier.STANDARD`:
- Free tier (no additional cost)
- Max 4KB value size
- Standard throughput

### Sensitive Data

**Important**: Sensitive credentials (API keys, passwords) are stored in AWS Secrets Manager, NOT Parameter Store:

```typescript
// Secrets Manager for sensitive data
this.geminiApiKeySecret = new secretsmanager.Secret(this, 'GeminiApiKeySecret', {
  secretName: getResourceName(config, 'gemini-api-key'),
});
```

## Usage Examples

### Reading Parameters in Lambda Functions

```python
import boto3

ssm = boto3.client('ssm')
environment = os.environ['ENVIRONMENT']
project = os.environ['PROJECT_NAME']

# Read configuration
response = ssm.get_parameter(
    Name=f'/{project}/{environment}/config/gemini-model'
)
model_name = response['Parameter']['Value']

# Read cross-stack resource
response = ssm.get_parameter(
    Name=f'/{project}/{environment}/storage/dynamodb/cache-table-name'
)
table_name = response['Parameter']['Value']
```

### Reading Parameters via AWS CLI

```bash
# Get API Gateway URL
aws ssm get-parameter \
  --name /co2-analysis/dev/compute/api-gateway/url \
  --query 'Parameter.Value' \
  --output text

# Get all storage parameters
aws ssm get-parameters-by-path \
  --path /co2-analysis/dev/storage \
  --recursive

# Get CloudFront distribution URL
aws ssm get-parameter \
  --name /co2-analysis/dev/frontend/cloudfront/distribution-url
```

### Reading Parameters in Other CDK Stacks

```typescript
import * as ssm from 'aws-cdk-lib/aws-ssm';

// Lookup at synthesis time
const apiUrl = ssm.StringParameter.valueFromLookup(
  this,
  '/co2-analysis/dev/compute/api-gateway/url'
);

// Import existing parameter
const parameter = ssm.StringParameter.fromStringParameterName(
  this,
  'ApiUrlParam',
  '/co2-analysis/dev/compute/api-gateway/url'
);
const value = parameter.stringValue;
```

## Deployment Order

Due to Parameter Store lookups, stacks must be deployed in dependency order:

```bash
# Deploy all stacks in order
cdk deploy --all --context environment=dev

# Or deploy individually
cdk deploy BaseStack --context environment=dev
cdk deploy NetworkStack --context environment=dev
cdk deploy StorageStack --context environment=dev
cdk deploy ComputeStack --context environment=dev
cdk deploy FrontendStack --context environment=dev
cdk deploy MonitoringStack --context environment=dev
```

**Important**: First-time deployment requires all stacks to be deployed together, as Parameter Store lookups depend on parameters being created.

## Verification

After deployment, verify Parameter Store integration:

```bash
# List all parameters for the environment
aws ssm describe-parameters \
  --parameter-filters "Key=Name,Option=BeginsWith,Values=/co2-analysis/dev/"

# Test parameter retrieval
aws ssm get-parameter --name /co2-analysis/dev/compute/api-gateway/url
aws ssm get-parameter --name /co2-analysis/dev/storage/dynamodb/cache-table-name
aws ssm get-parameter --name /co2-analysis/dev/frontend/cloudfront/distribution-url
```

## Environment-Specific Parameters

Parameters are isolated per environment:

```
Development:   /co2-analysis/dev/*
Staging:       /co2-analysis/staging/*
Production:    /co2-analysis/prod/*
```

This ensures complete isolation between environments.

## CloudFormation Outputs

Each stack also exports key values as CloudFormation outputs for backward compatibility:

```yaml
Outputs:
  ApiUrl:
    Value: !GetAtt ReasoningApi.Url
    Export:
      Name: co2-analysis-dev-api-url
```

These can be imported using `Fn.importValue()` in other CloudFormation stacks.

## Troubleshooting

### Parameter Not Found

If you encounter "Parameter not found" errors:

1. Verify the parameter exists:
   ```bash
   aws ssm get-parameter --name /co2-analysis/dev/storage/dynamodb/cache-table-name
   ```

2. Check IAM permissions for the calling service

3. Ensure the stack creating the parameter was deployed successfully

### Lookup Context Caching

CDK caches parameter lookups. To force refresh:

```bash
# Clear context cache
rm cdk.context.json

# Re-synthesize
cdk synth --context environment=dev
```

### Cross-Region Parameters

Parameter Store is region-specific. Ensure your stacks are deployed in the same region as the parameters.

## Best Practices

1. **Naming Consistency**: Always use `getResourceName()` utility for consistent naming
2. **Type Safety**: Prefer direct props passing for CDK resources
3. **Runtime Access**: Use Parameter Store for runtime configuration
4. **Secrets Management**: Never store sensitive data in Parameter Store; use Secrets Manager
5. **Parameter Documentation**: Always include descriptive `description` field
6. **Scoped IAM**: Limit Parameter Store permissions to specific paths
7. **Environment Isolation**: Keep parameters segregated by environment

## Cost Considerations

- **Standard Parameters**: Free (up to 10,000 parameters)
- **Parameter Storage**: No charge for storage
- **API Calls**: Standard Parameter Store API calls are free within AWS service limits

## Future Enhancements

Potential improvements for future iterations:

1. **Parameter Encryption**: Use KMS-encrypted SecureString parameters for additional security
2. **Parameter History**: Enable versioning for configuration auditing
3. **Cross-Region Replication**: Implement parameter replication for DR scenarios
4. **Automated Testing**: Add integration tests to verify parameter accessibility
5. **Parameter Validation**: Implement CloudFormation custom resources for parameter validation

## Related Documentation

- [AWS Systems Manager Parameter Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html)
- [CDK Parameter Store Constructs](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_ssm-readme.html)
- [Cross-Stack References in CDK](https://docs.aws.amazon.com/cdk/v2/guide/resources.html#resource_stack)

---

**Created**: Task 9[P] - Parameter Store Integration
**Last Updated**: 2025-11-01
