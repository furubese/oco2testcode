# Parameter Store Quick Reference

## Quick Access Table

### All Exported Parameters by Stack

#### BaseStack - Configuration Parameters

```bash
/co2-analysis/{env}/config/gemini-model
/co2-analysis/{env}/config/cache-ttl-days
/co2-analysis/{env}/config/function-timeout-seconds
```

#### StorageStack - DynamoDB & S3

```bash
# DynamoDB
/co2-analysis/{env}/storage/dynamodb/cache-table-name
/co2-analysis/{env}/storage/dynamodb/cache-table-arn

# S3 - GeoJSON Bucket
/co2-analysis/{env}/storage/s3/geojson-bucket-name
/co2-analysis/{env}/storage/s3/geojson-bucket-arn

# S3 - Website Bucket
/co2-analysis/{env}/storage/s3/website-bucket-name
/co2-analysis/{env}/storage/s3/website-bucket-arn
```

#### ComputeStack - Lambda & API Gateway

```bash
# API Gateway
/co2-analysis/{env}/compute/api-gateway/url
/co2-analysis/{env}/compute/api-gateway/id
/co2-analysis/{env}/compute/api-gateway/stage

# Lambda Function
/co2-analysis/{env}/compute/lambda/function-arn
/co2-analysis/{env}/compute/lambda/function-name
```

#### FrontendStack - CloudFront & S3

```bash
# CloudFront
/co2-analysis/{env}/frontend/cloudfront/distribution-url
/co2-analysis/{env}/frontend/cloudfront/distribution-domain
/co2-analysis/{env}/frontend/cloudfront/distribution-id

# S3
/co2-analysis/{env}/frontend/s3/website-bucket-name
```

#### MonitoringStack - CloudWatch & SNS

```bash
# SNS
/co2-analysis/{env}/monitoring/sns/alarm-topic-arn

# CloudWatch
/co2-analysis/{env}/monitoring/cloudwatch/dashboard-name
```

---

## Common Commands

### List All Parameters for Environment

```bash
# Development
aws ssm get-parameters-by-path \
  --path /co2-analysis/dev \
  --recursive

# Production
aws ssm get-parameters-by-path \
  --path /co2-analysis/prod \
  --recursive
```

### Get Specific Parameter

```bash
# Get API URL
aws ssm get-parameter \
  --name /co2-analysis/dev/compute/api-gateway/url \
  --query 'Parameter.Value' \
  --output text

# Get DynamoDB Table Name
aws ssm get-parameter \
  --name /co2-analysis/dev/storage/dynamodb/cache-table-name \
  --query 'Parameter.Value' \
  --output text

# Get CloudFront URL
aws ssm get-parameter \
  --name /co2-analysis/dev/frontend/cloudfront/distribution-url \
  --query 'Parameter.Value' \
  --output text
```

### Get Multiple Parameters at Once

```bash
# Get all storage parameters
aws ssm get-parameters \
  --names \
    /co2-analysis/dev/storage/dynamodb/cache-table-name \
    /co2-analysis/dev/storage/s3/geojson-bucket-name \
    /co2-analysis/dev/storage/s3/website-bucket-name \
  --query 'Parameters[*].[Name,Value]' \
  --output table
```

---

## Python Usage Examples

### Basic Parameter Retrieval

```python
import boto3
import os

ssm = boto3.client('ssm')
environment = os.environ.get('ENVIRONMENT', 'dev')

def get_parameter(param_name):
    response = ssm.get_parameter(
        Name=f'/co2-analysis/{environment}/{param_name}'
    )
    return response['Parameter']['Value']

# Examples
api_url = get_parameter('compute/api-gateway/url')
table_name = get_parameter('storage/dynamodb/cache-table-name')
gemini_model = get_parameter('config/gemini-model')
```

### Batch Parameter Retrieval

```python
def get_parameters_by_path(path_segment):
    response = ssm.get_parameters_by_path(
        Path=f'/co2-analysis/{environment}/{path_segment}',
        Recursive=True
    )
    return {
        param['Name'].split('/')[-1]: param['Value']
        for param in response['Parameters']
    }

# Get all storage parameters
storage_params = get_parameters_by_path('storage')
# Returns: {'cache-table-name': '...', 'geojson-bucket-name': '...', ...}
```

### Caching Parameters (Performance Optimization)

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_cached_parameter(param_name):
    """Cache parameter values to reduce SSM API calls"""
    response = ssm.get_parameter(
        Name=f'/co2-analysis/{environment}/{param_name}'
    )
    return response['Parameter']['Value']

# Usage
api_url = get_cached_parameter('compute/api-gateway/url')
```

---

## TypeScript/CDK Usage Examples

### Reading Parameters in CDK Stacks

```typescript
import * as ssm from 'aws-cdk-lib/aws-ssm';

// Lookup at synthesis time (cached in cdk.context.json)
const apiUrl = ssm.StringParameter.valueFromLookup(
  this,
  '/co2-analysis/dev/compute/api-gateway/url'
);

// Import existing parameter as construct
const apiUrlParam = ssm.StringParameter.fromStringParameterName(
  this,
  'ApiUrlParameter',
  '/co2-analysis/dev/compute/api-gateway/url'
);
const url = apiUrlParam.stringValue;
```

### Creating New Parameters

```typescript
const parameter = new ssm.StringParameter(this, 'MyParameter', {
  parameterName: `/co2-analysis/${config.environment}/my-stack/my-resource`,
  stringValue: 'my-value',
  description: 'Description of the parameter',
  tier: ssm.ParameterTier.STANDARD,
});
```

---

## Environment Variables for Lambda

Parameters are passed to Lambda via environment variables in ComputeStack:

```typescript
environment: {
  DYNAMODB_TABLE_NAME: props.cacheTable.tableName,
  GEMINI_SECRET_NAME: props.geminiApiKeySecret.secretName,
  ENVIRONMENT: config.environment,
  PROJECT_NAME: config.projectName,
  PARAMETER_STORE_PATH: `/${config.projectName}/${config.environment}/config`,
}
```

Lambda can then read additional parameters at runtime:

```python
import boto3
import os

ssm = boto3.client('ssm')
parameter_path = os.environ['PARAMETER_STORE_PATH']

# Read configuration
gemini_model = ssm.get_parameter(
    Name=f'{parameter_path}/gemini-model'
)['Parameter']['Value']
```

---

## Cross-Stack Dependencies

### Stack Dependencies (via Props)

```
BaseStack (Layer 1)
  ├─> NetworkStack (Layer 2)
  ├─> StorageStack (Layer 3)
  │     └─> ComputeStack (Layer 4)
  │     └─> FrontendStack (Layer 5)
  │           └─> MonitoringStack (Layer 6)
  └─> ComputeStack (Layer 4)
        └─> MonitoringStack (Layer 6)
```

### Parameter Store Dependencies

- **ComputeStack** reads: `/storage/dynamodb/cache-table-name`
- **FrontendStack** reads: `/compute/api-gateway/url`

---

## IAM Permission Required

### For Lambda Functions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParametersByPath"
      ],
      "Resource": "arn:aws:ssm:*:*:parameter/co2-analysis/*"
    }
  ]
}
```

Already configured in BaseStack Lambda Execution Role.

---

## Naming Pattern

```
/{projectName}/{environment}/{stack}/{resourceType}/{parameterName}
```

Example breakdown:
```
/co2-analysis/dev/storage/dynamodb/cache-table-name
 └────┬────┘ └┬┘ └──┬──┘ └───┬───┘ └──────┬────────┘
  project    env  stack   type         name
```

---

## Troubleshooting

### "Parameter not found"

1. Check parameter exists:
   ```bash
   aws ssm describe-parameters | grep co2-analysis
   ```

2. Verify you're in the correct region:
   ```bash
   aws configure get region
   ```

3. Check IAM permissions

### "Access Denied"

Ensure the caller has `ssm:GetParameter` permission for the specific parameter path.

### CDK Lookup Issues

Clear CDK context cache:
```bash
rm cdk.context.json
cdk synth --context environment=dev
```

---

## Cost Information

- **Standard Parameters**: Free (10,000 parameter limit per account)
- **API Calls**: First 1,000,000 parameter store API calls/month are free
- **Storage**: No charge

---

## Security Best Practices

1. ✅ **Use Parameter Store for**: Configuration values, ARNs, resource names
2. ❌ **Never use Parameter Store for**: Passwords, API keys, credentials
3. ✅ **Use Secrets Manager for**: All sensitive credentials
4. ✅ **Limit IAM permissions**: Scope to specific parameter paths
5. ✅ **Use environment prefixes**: Keep dev/staging/prod isolated

---

## Complete Example: Full Integration

```python
import boto3
import os

class ConfigManager:
    def __init__(self):
        self.ssm = boto3.client('ssm')
        self.secrets = boto3.client('secretsmanager')
        self.environment = os.environ['ENVIRONMENT']
        self.project = os.environ['PROJECT_NAME']

    def get_config(self, path):
        """Get configuration from Parameter Store"""
        full_path = f'/{self.project}/{self.environment}/{path}'
        response = self.ssm.get_parameter(Name=full_path)
        return response['Parameter']['Value']

    def get_secret(self, secret_name):
        """Get secret from Secrets Manager"""
        response = self.secrets.get_secret_value(SecretId=secret_name)
        return response['SecretString']

    def get_all_config(self):
        """Get all configuration as a dict"""
        return {
            # From Parameter Store
            'gemini_model': self.get_config('config/gemini-model'),
            'cache_ttl': self.get_config('config/cache-ttl-days'),
            'table_name': self.get_config('storage/dynamodb/cache-table-name'),

            # From Environment Variables (set by CDK)
            'environment': os.environ['ENVIRONMENT'],

            # From Secrets Manager
            'gemini_api_key': self.get_secret(os.environ['GEMINI_SECRET_NAME'])
        }

# Usage
config = ConfigManager()
all_config = config.get_all_config()
```

---

**Last Updated**: 2025-11-01
**Task**: Task 9[P] - Parameter Store Integration
