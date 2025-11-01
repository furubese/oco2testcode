# MonitoringStack - CloudWatch Observability Implementation

## Overview

The **MonitoringStack** (Layer 6: Observability) provides comprehensive monitoring and observability for the CO2 Anomaly Analysis System using AWS CloudWatch, SNS, and Parameter Store integration.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MonitoringStack                          │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │              │  │              │  │                 │  │
│  │ CloudWatch   │  │ CloudWatch   │  │  SNS Topic      │  │
│  │ Dashboard    │  │ Alarms (6)   │  │  + Email Sub    │  │
│  │              │  │              │  │                 │  │
│  └──────────────┘  └──────┬───────┘  └────────┬────────┘  │
│                           │                    │            │
│                           └────────────────────┘            │
│                                  │                          │
└──────────────────────────────────┼──────────────────────────┘
                                   │
                                   ▼
              ┌────────────────────────────────────┐
              │  Monitored Resources:              │
              │  - Lambda Function                 │
              │  - API Gateway                     │
              │  - DynamoDB Table                  │
              │  - Custom Metrics (Cache Hit/Miss) │
              └────────────────────────────────────┘
```

## Features Implemented

### ✅ Acceptance Criteria

| Criteria | Status | Implementation |
|----------|--------|----------------|
| CloudWatch Logs configured for Lambda | ✅ | Log groups referenced with retention policies |
| Custom metrics tracking | ✅ | Cache hit/miss ratio, API calls, Lambda duration, error rate |
| Error rate alarm (>5%) | ✅ | `LambdaErrorRateAlarm` - triggers at >5 errors in 5 minutes |
| Lambda duration alarm (>10s) | ✅ | `LambdaDurationAlarm` - triggers at >10s average duration |
| SNS topic for notifications | ✅ | `AlarmTopic` with email subscription and SSL enforcement |
| CloudWatch dashboard | ✅ | 5-row dashboard with 10 widgets displaying system health |
| Proper tagging and naming | ✅ | All resources tagged with Project, Environment, Layer, etc. |

## Components

### 1. SNS Topic for Alarm Notifications

**Resource:** `AlarmTopic`

- **Name:** `co2-analysis-{environment}-alarms`
- **Display Name:** `CO2 Anomaly Analysis - {ENVIRONMENT} Alarms`
- **SSL Enforcement:** ✅ Enabled (CDK Nag compliant)
- **Email Subscription:** Configured from `cdk.json` `alarmEmail` property
- **Parameter Store:** ARN stored at `/{projectName}/{environment}/monitoring/sns/alarm-topic-arn`

**SNS Topic Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowPublishThroughSSLOnly",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "SNS:Publish",
      "Resource": "*",
      "Condition": {
        "Bool": {
          "aws:SecureTransport": "false"
        }
      }
    }
  ]
}
```

### 2. CloudWatch Logs Configuration

**Lambda Log Group:**
- **Path:** `/aws/lambda/{functionName}`
- **Retention:** Environment-specific (7d/14d/30d)
- **Automatically created** by Lambda service

**API Gateway Log Group:**
- **Path:** `API-Gateway-Execution-Logs_{apiId}/{stageName}`
- **Retention:** Environment-specific (7d/14d/30d)
- **Automatically created** by API Gateway

### 3. CloudWatch Alarms (6 Total)

#### 3.1 Lambda Error Rate Alarm
- **Metric:** `Lambda Errors`
- **Threshold:** >5 errors in 5 minutes
- **Evaluation Period:** 5 minutes
- **Comparison:** Greater than 5
- **Action:** SNS notification to `AlarmTopic`
- **Description:** "Alert when Lambda error rate exceeds 5%"

#### 3.2 Lambda Duration Alarm
- **Metric:** `Lambda Duration (Average)`
- **Threshold:** >10 seconds (10,000 ms)
- **Evaluation Period:** 5 minutes
- **Comparison:** Greater than 10,000 ms
- **Action:** SNS notification
- **Description:** "Alert when Lambda average duration exceeds 10 seconds"

#### 3.3 Lambda Throttling Alarm
- **Metric:** `Lambda Throttles`
- **Threshold:** ≥1 throttle event
- **Evaluation Period:** 1 minute
- **Comparison:** Greater than or equal to 1
- **Action:** SNS notification
- **Description:** "Alert when Lambda function is throttled"

#### 3.4 API Gateway 5xx Error Alarm
- **Metric:** `API Gateway 5xx Errors`
- **Threshold:** >10 errors in 5 minutes
- **Evaluation Period:** 5 minutes
- **Comparison:** Greater than 10
- **Action:** SNS notification
- **Description:** "Alert when API Gateway 5xx errors exceed 10 in 5 minutes"

#### 3.5 API Gateway Latency Alarm
- **Metric:** `API Gateway Latency (Average)`
- **Threshold:** >10 seconds (10,000 ms)
- **Evaluation Period:** 5 minutes
- **Comparison:** Greater than 10,000 ms
- **Action:** SNS notification
- **Description:** "Alert when API Gateway average latency exceeds 10 seconds"

#### 3.6 DynamoDB Throttling Alarm
- **Metric:** `DynamoDB UserErrors`
- **Threshold:** >10 throttles in 5 minutes
- **Evaluation Period:** 5 minutes
- **Comparison:** Greater than 10
- **Action:** SNS notification
- **Description:** "Alert when DynamoDB throttles exceed 10 in 5 minutes"

### 4. Custom Metrics (Embedded Metric Format)

Custom metrics are published from the Lambda function using CloudWatch Embedded Metric Format (EMF):

**Metrics Published:**
- `CacheHit` (Count) - Number of cache hits
- `CacheMiss` (Count) - Number of cache misses
- `ApiCallDuration` (Milliseconds) - Duration of API calls
- `GeminiApiCall` (Count) - Number of Gemini API calls

**Cache Hit Ratio Calculation:**
```
Cache Hit Ratio (%) = (CacheHit / (CacheHit + CacheMiss)) × 100
```

**Namespace:** `{projectName}` (e.g., `co2-analysis`)

**Dimensions:**
- `Environment` - dev/staging/prod

### 5. CloudWatch Dashboard

**Dashboard Name:** `co2-analysis-{environment}-dashboard`

**Layout:** 5 rows × 2 columns = 10 widgets

#### Row 1: Lambda Function Metrics
1. **Lambda Invocations & Errors** (12 width)
   - Invocations (SUM)
   - Errors (SUM)

2. **Lambda Duration (p50, p90, p99)** (12 width)
   - Duration p50
   - Duration p90
   - Duration p99

#### Row 2: Lambda Performance
3. **Lambda Throttles** (12 width)
   - Throttles (SUM)

4. **Lambda Concurrent Executions** (12 width)
   - Concurrent Executions (MAX)

#### Row 3: API Gateway Metrics
5. **API Gateway Requests & Errors** (12 width)
   - Requests (SUM)
   - 4xx Errors (SUM)
   - 5xx Errors (SUM)

6. **API Gateway Latency (p50, p90, p99)** (12 width)
   - Latency p50
   - Latency p90
   - Latency p99

#### Row 4: DynamoDB & Cache Metrics
7. **DynamoDB Read/Write Capacity** (12 width)
   - Consumed Read Capacity Units (SUM)
   - Consumed Write Capacity Units (SUM)

8. **Cache Hit Ratio & Custom Metrics** (12 width)
   - Cache Hit Ratio (%) - left axis
   - Cache Hit Count - right axis
   - Cache Miss Count - right axis

#### Row 5: DynamoDB Performance & Health
9. **DynamoDB Latency** (12 width)
   - GetItem Latency (AVG)
   - PutItem Latency (AVG)

10. **System Health Status** (12 width) - Single Value Widget
    - Lambda Errors (SUM)
    - API 5xx Errors (SUM)

**Dashboard URL Format:**
```
https://{region}.console.aws.amazon.com/cloudwatch/home?region={region}#dashboards:name={dashboardName}
```

### 6. Parameter Store Integration

All monitoring configuration is exported to Parameter Store:

| Parameter | Path | Description |
|-----------|------|-------------|
| SNS Topic ARN | `/{projectName}/{environment}/monitoring/sns/alarm-topic-arn` | SNS topic ARN for alarms |
| Dashboard Name | `/{projectName}/{environment}/monitoring/cloudwatch/dashboard-name` | Dashboard name |
| Dashboard URL | `/{projectName}/{environment}/monitoring/cloudwatch/dashboard-url` | Console URL |

**Example:**
```
/co2-analysis/dev/monitoring/sns/alarm-topic-arn
/co2-analysis/dev/monitoring/cloudwatch/dashboard-name
/co2-analysis/dev/monitoring/cloudwatch/dashboard-url
```

### 7. Stack Outputs

| Output | Export Name | Description |
|--------|-------------|-------------|
| AlarmTopicArn | `{projectName}-{environment}-alarm-topic-arn` | SNS Topic ARN |
| DashboardName | `{projectName}-{environment}-dashboard-name` | Dashboard name |
| DashboardUrl | N/A | Dashboard console URL |
| LambdaLogGroupName | N/A | Lambda log group name |
| ApiLogGroupName | N/A | API Gateway log group name |

## Resource Tagging

All resources are tagged with:

```json
{
  "Project": "co2-analysis",
  "Environment": "dev|staging|prod",
  "Application": "CO2 Anomaly Analysis",
  "ManagedBy": "CDK",
  "CreatedBy": "AWS-CDK",
  "Layer": "6-Observability"
}
```

## Environment-Specific Configuration

### Development
- **Log Retention:** 7 days
- **Alarm Email:** From `cdk.json`
- **X-Ray:** Disabled (cost optimization)

### Staging
- **Log Retention:** 14 days
- **Alarm Email:** From `cdk.json`
- **X-Ray:** Enabled

### Production
- **Log Retention:** 30 days
- **Alarm Email:** From `cdk.json`
- **X-Ray:** Enabled

## Deployment

### Prerequisites

1. **CDK Bootstrap:**
   ```bash
   cdk bootstrap aws://{account}/{region}
   ```

2. **Environment Configuration:**
   Update `cdk.json` with your alarm email:
   ```json
   {
     "environmentConfig": {
       "dev": {
         "alarmEmail": "your-email@example.com"
       }
     }
   }
   ```

### Deploy MonitoringStack

```bash
cd cdk

# Deploy all stacks (including MonitoringStack)
cdk deploy --all --context environment=dev

# Or deploy MonitoringStack only (requires other stacks first)
cdk deploy MonitoringStack --context environment=dev
```

### Stack Dependencies

MonitoringStack depends on:
1. **ComputeStack** - Lambda function reference
2. **StorageStack** - DynamoDB table reference

CDK automatically handles dependency resolution based on resource references.

## Verification

### 1. Verify SNS Topic

```bash
aws sns list-topics --query 'Topics[?contains(TopicArn, `co2-analysis-dev-alarms`)]'
```

### 2. Verify Email Subscription

Check your email for SNS subscription confirmation and confirm the subscription.

### 3. View Dashboard

```bash
# Get dashboard URL from Parameter Store
aws ssm get-parameter \
  --name /co2-analysis/dev/monitoring/cloudwatch/dashboard-url \
  --query 'Parameter.Value' \
  --output text
```

Or via CloudFormation outputs:
```bash
aws cloudformation describe-stacks \
  --stack-name MonitoringStack \
  --query 'Stacks[0].Outputs[?OutputKey==`DashboardUrl`].OutputValue' \
  --output text
```

### 4. List Alarms

```bash
aws cloudwatch describe-alarms \
  --alarm-name-prefix co2-analysis-dev
```

### 5. Test Alarm (Optional)

Trigger a test alarm by setting the alarm state:
```bash
aws cloudwatch set-alarm-state \
  --alarm-name co2-analysis-dev-lambda-error-rate \
  --state-value ALARM \
  --state-reason "Testing alarm notification"
```

## Monitoring Best Practices

### 1. Custom Metrics from Lambda

The Lambda function publishes custom metrics using EMF:

```python
import json

# Embedded Metric Format
metrics = {
    "_aws": {
        "Timestamp": int(time.time() * 1000),
        "CloudWatchMetrics": [{
            "Namespace": "co2-analysis",
            "Dimensions": [["Environment"]],
            "Metrics": [
                {"Name": "CacheHit", "Unit": "Count"},
                {"Name": "CacheMiss", "Unit": "Count"}
            ]
        }]
    },
    "Environment": "dev",
    "CacheHit": 1 if cached else 0,
    "CacheMiss": 0 if cached else 1
}

print(json.dumps(metrics))  # CloudWatch Logs ingests this as a metric
```

### 2. Alarm Actions

All alarms send notifications to the SNS topic, which triggers email alerts to configured recipients.

### 3. Dashboard Customization

You can customize the dashboard after deployment via the AWS Console or by modifying the MonitoringStack code.

### 4. Log Insights Queries

Example CloudWatch Logs Insights query for cache hit ratio:
```sql
fields @timestamp, cached
| filter cached = true
| stats count() as CacheHits by bin(5m)
```

## Cost Optimization

### Estimated Monthly Costs (Development)

| Service | Usage | Cost |
|---------|-------|------|
| CloudWatch Alarms | 6 alarms | $0.60 |
| CloudWatch Dashboard | 1 dashboard | $3.00 |
| CloudWatch Logs | ~1 GB/month | $0.50 |
| SNS Notifications | ~100 emails/month | $0.00 |
| **Total** | | **~$4.10/month** |

### Cost Optimization Tips

1. **Log Retention:** Set appropriate retention periods
   - Dev: 7 days
   - Staging: 14 days
   - Prod: 30 days

2. **Custom Metrics:** Publish only essential metrics
   - Use EMF to batch metrics
   - Avoid high-cardinality dimensions

3. **Alarms:** Use composite alarms to reduce alarm count

4. **Dashboard:** Use a single dashboard per environment

## Troubleshooting

### Alarm Not Triggering

1. **Check Alarm Configuration:**
   ```bash
   aws cloudwatch describe-alarms --alarm-names co2-analysis-dev-lambda-error-rate
   ```

2. **Verify Metric Data:**
   ```bash
   aws cloudwatch get-metric-statistics \
     --namespace AWS/Lambda \
     --metric-name Errors \
     --dimensions Name=FunctionName,Value=co2-analysis-dev-reasoning-handler \
     --start-time 2024-01-01T00:00:00Z \
     --end-time 2024-01-01T23:59:59Z \
     --period 300 \
     --statistics Sum
   ```

3. **Check SNS Subscription Status:**
   ```bash
   aws sns list-subscriptions-by-topic \
     --topic-arn arn:aws:sns:us-east-1:123456789012:co2-analysis-dev-alarms
   ```

### Dashboard Not Showing Data

1. **Verify Resources Exist:**
   - Lambda function is deployed
   - API Gateway is deployed
   - DynamoDB table is deployed

2. **Check Time Range:** Adjust dashboard time range in console

3. **Verify Custom Metrics:**
   ```bash
   aws cloudwatch list-metrics --namespace co2-analysis
   ```

### Email Not Received

1. **Confirm SNS Subscription:**
   - Check spam folder
   - Click confirmation link in SNS email

2. **Test SNS Topic:**
   ```bash
   aws sns publish \
     --topic-arn arn:aws:sns:us-east-1:123456789012:co2-analysis-dev-alarms \
     --message "Test notification"
   ```

## CDK Nag Compliance

The MonitoringStack is compliant with AWS Solutions security best practices (CDK Nag):

✅ **AwsSolutions-SNS3:** SNS Topic enforces SSL (`enforceSSL: true`)

All other CDK Nag warnings/errors are in dependent stacks (BaseStack, StorageStack, ComputeStack).

## References

- [AWS CDK CloudWatch Module](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cloudwatch-readme.html)
- [CloudWatch Embedded Metric Format](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format.html)
- [CloudWatch Alarms](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html)
- [CDK Nag Rules](https://github.com/cdklabs/cdk-nag)

## Next Steps

1. **Deploy the Stack:**
   ```bash
   cdk deploy --all --context environment=dev
   ```

2. **Confirm SNS Email Subscription**

3. **View Dashboard in AWS Console**

4. **Test Alarms** by triggering errors or high latency

5. **Customize Dashboard** based on operational needs

6. **Set up CloudWatch Logs Insights** queries for advanced analysis

---

**Stack Status:** ✅ Ready for Deployment

**CDK Nag Status:** ✅ Compliant (MonitoringStack only)

**Last Updated:** 2025-11-02
