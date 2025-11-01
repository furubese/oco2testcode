# MonitoringStack - CloudWatch Observability Layer

## Overview

The MonitoringStack implements comprehensive monitoring and observability for the CO2 Anomaly Analysis System using AWS CloudWatch. This stack is Layer 6 in the architecture and provides real-time visibility into system health, performance metrics, and operational alerts.

## Features

### 1. CloudWatch Logs
- **Lambda Function Logs**: Automatic log collection with configurable retention periods
  - Development: 7 days
  - Staging: 14 days
  - Production: 30 days
- **Structured Logging**: JSON-formatted logs from Lambda functions
- **Encryption**: AWS-managed encryption for all log data

### 2. Custom Metrics

The stack implements metric filters to track application-specific events:

#### Cache Performance Metrics
- **Cache Hit**: Tracks successful cache retrievals
- **Cache Miss**: Tracks cache misses requiring API calls
- **Cache Hit Ratio**: Calculated metric showing cache efficiency (%)

#### API Call Metrics
- **Gemini API Calls**: Tracks calls to Google Gemini API
- **API Call Rate**: Rate of API invocations

#### Error Tracking
- **Application Errors**: Tracks errors logged by the Lambda function
- **Error Rate**: Percentage of invocations resulting in errors

#### Lambda Performance Metrics
- **Duration**: Average execution time (milliseconds)
- **Invocations**: Total number of function invocations
- **Throttles**: Number of throttled requests
- **Concurrent Executions**: Number of concurrent function executions

#### DynamoDB Metrics
- **Consumed Read Capacity**: DynamoDB read capacity units consumed
- **Consumed Write Capacity**: DynamoDB write capacity units consumed
- **User Errors**: DynamoDB throttling events

### 3. CloudWatch Alarms

The stack creates six critical alarms with SNS notifications:

#### 1. Error Rate Alarm
- **Threshold**: >5% error rate
- **Evaluation**: 2 consecutive periods of 5 minutes
- **Action**: SNS notification
- **Purpose**: Detect sustained error conditions

#### 2. Lambda Duration Alarm
- **Threshold**: >10 seconds average duration
- **Evaluation**: 2 consecutive periods of 1 minute
- **Action**: SNS notification
- **Purpose**: Detect performance degradation

#### 3. Lambda Errors Alarm
- **Threshold**: >5 errors in 5 minutes
- **Evaluation**: 1 period
- **Action**: SNS notification
- **Purpose**: Rapid detection of error spikes

#### 4. Lambda Throttles Alarm
- **Threshold**: ≥1 throttle event
- **Evaluation**: 1 period of 5 minutes
- **Action**: SNS notification
- **Purpose**: Detect concurrency limits

#### 5. DynamoDB Throttles Alarm
- **Threshold**: >10 throttles in 5 minutes
- **Evaluation**: 1 period
- **Action**: SNS notification
- **Purpose**: Detect capacity issues

#### 6. Cache Hit Ratio Alarm
- **Threshold**: <50% cache hit ratio
- **Evaluation**: 2 out of 3 periods of 5 minutes
- **Action**: SNS notification
- **Purpose**: Detect cache efficiency problems

### 4. SNS Topic for Notifications

- **Topic Name**: `{projectName}-{environment}-alarm-topic`
- **Display Name**: `{appName} - {environment} Alarms`
- **SSL Enforcement**: Enabled
- **Email Subscription**: Configured via `alarmEmail` in environment config
- **Parameter Store Export**: SNS topic ARN stored for cross-stack reference

### 5. CloudWatch Dashboard

A comprehensive operational dashboard with the following widgets:

#### Row 1: Lambda Performance
- Lambda Invocations (count)
- Lambda Duration (milliseconds)
- Lambda Errors & Throttles (count)

#### Row 2: Error Rate and Cache Performance
- Error Rate (percentage)
- Cache Hit/Miss (count)
- Cache Hit Ratio (percentage)

#### Row 3: DynamoDB Metrics
- DynamoDB Consumed Capacity (read/write units)
- DynamoDB Throttles (count)

#### Row 4: API Calls and Custom Metrics
- Gemini API Calls (count)
- Application Errors (count)

#### Row 5: Alarm Status
- Real-time status of all CloudWatch alarms

## Architecture

```
MonitoringStack
├── SNS Topic (alarm-topic)
│   ├── Email Subscription (optional)
│   └── Parameter Store Export
├── CloudWatch Logs
│   ├── Lambda Log Group (/aws/lambda/{functionName})
│   └── Metric Filters
│       ├── CacheHit
│       ├── CacheMiss
│       ├── GeminiApiCalls
│       └── Errors
├── CloudWatch Alarms (6 total)
│   ├── ErrorRateAlarm
│   ├── DurationAlarm
│   ├── LambdaErrorsAlarm
│   ├── ThrottlesAlarm
│   ├── DynamoThrottlesAlarm
│   └── CacheHitRatioAlarm
└── CloudWatch Dashboard
    ├── Lambda Performance Widgets
    ├── Error & Cache Widgets
    ├── DynamoDB Widgets
    ├── API Call Widgets
    └── Alarm Status Widget
```

## Dependencies

The MonitoringStack depends on:
- **ComputeStack**: Provides the Lambda function to monitor
- **StorageStack**: Provides the DynamoDB table to monitor

## Parameter Store Integration

The stack exports the following parameters:

| Parameter Name | Description | Example Value |
|---------------|-------------|---------------|
| `/co2-analysis/{env}/monitoring/sns/alarm-topic-arn` | SNS topic ARN for alarms | `arn:aws:sns:us-east-1:123456789012:co2-analysis-dev-alarm-topic` |
| `/co2-analysis/{env}/monitoring/cloudwatch/dashboard-name` | Dashboard name | `co2-analysis-dev-operational-dashboard` |

## Environment-Specific Configuration

Configuration is controlled via `cdk.json`:

```json
{
  "environmentConfig": {
    "dev": {
      "logRetentionDays": 7,
      "alarmEmail": "",
      "enableXRay": false
    },
    "staging": {
      "logRetentionDays": 14,
      "alarmEmail": "staging-alerts@example.com",
      "enableXRay": true
    },
    "prod": {
      "logRetentionDays": 30,
      "alarmEmail": "prod-alerts@example.com",
      "enableXRay": true
    }
  }
}
```

## Deployment

### Prerequisites
1. ComputeStack deployed (provides Lambda function)
2. StorageStack deployed (provides DynamoDB table)
3. Email address configured in `cdk.json` for alarm notifications (optional)

### Deploy Command
```bash
# Deploy MonitoringStack only
npm run cdk:deploy:monitoring

# Or deploy all stacks
npm run cdk:deploy
```

### Verify Deployment
```bash
# Check stack status
aws cloudformation describe-stacks \
  --stack-name MonitoringStack \
  --region us-east-1

# Get dashboard URL
aws ssm get-parameter \
  --name /co2-analysis/dev/monitoring/cloudwatch/dashboard-name \
  --region us-east-1

# Get SNS topic ARN
aws ssm get-parameter \
  --name /co2-analysis/dev/monitoring/sns/alarm-topic-arn \
  --region us-east-1
```

## Accessing the Dashboard

### Via AWS Console
1. Navigate to CloudWatch Console
2. Select "Dashboards" from the left menu
3. Click on `co2-analysis-{environment}-operational-dashboard`

### Via CloudFormation Output
```bash
aws cloudformation describe-stacks \
  --stack-name MonitoringStack \
  --query 'Stacks[0].Outputs[?OutputKey==`DashboardUrl`].OutputValue' \
  --output text
```

### Direct URL Format
```
https://console.aws.amazon.com/cloudwatch/home?region={region}#dashboards:name={dashboardName}
```

## Alarm Notification Setup

### Confirming Email Subscription
After deployment, if `alarmEmail` is configured:
1. Check your email inbox
2. Look for "AWS Notification - Subscription Confirmation"
3. Click the confirmation link
4. You will receive alarm notifications at this email

### Adding Additional Subscribers
```bash
# Add another email subscription
aws sns subscribe \
  --topic-arn $(aws ssm get-parameter \
    --name /co2-analysis/dev/monitoring/sns/alarm-topic-arn \
    --query 'Parameter.Value' \
    --output text) \
  --protocol email \
  --notification-endpoint another-email@example.com
```

## Monitoring Best Practices

### 1. Alarm Tuning
- **Error Rate Threshold (5%)**: Adjust based on baseline error patterns
- **Duration Threshold (10s)**: Tune based on average API response times
- **Cache Hit Ratio (50%)**: Increase threshold after cache warming

### 2. Dashboard Usage
- Review dashboard daily during initial deployment
- Set up automated screenshot exports for reporting
- Use dashboard widgets in presentations

### 3. Metric Analysis
- Correlate cache hit ratio with API costs
- Monitor error rate trends over time
- Track Lambda duration against API latency

### 4. Cost Optimization
- CloudWatch Logs: ~$0.50/GB ingested
- CloudWatch Metrics: Free for AWS service metrics, $0.30/custom metric/month
- CloudWatch Alarms: $0.10/alarm/month
- CloudWatch Dashboards: $3/dashboard/month

Estimated monthly cost for dev environment: **~$5-10/month**

## Troubleshooting

### Alarms Not Firing
1. Check alarm state: `aws cloudwatch describe-alarms`
2. Verify metric data: `aws cloudwatch get-metric-statistics`
3. Confirm SNS subscription is confirmed
4. Check alarm configuration thresholds

### Missing Metrics
1. Verify Lambda function is being invoked
2. Check CloudWatch Logs for log entries
3. Confirm metric filters are correctly configured
4. Allow 5-10 minutes for metric data to appear

### Email Notifications Not Received
1. Verify SNS subscription is confirmed
2. Check spam/junk folders
3. Verify email address in configuration
4. Test SNS topic: `aws sns publish --topic-arn <arn> --message "Test"`

### Dashboard Not Showing Data
1. Confirm resources are deployed and active
2. Check time range selector (default: last 3 hours)
3. Verify metrics exist: `aws cloudwatch list-metrics`
4. Refresh browser cache

## Testing

### Unit Tests
```bash
# Run all tests
npm test

# Run MonitoringStack tests only
npm test -- monitoring-stack.test.ts

# Run tests with coverage
npm test -- --coverage
```

### Integration Testing
```bash
# Trigger Lambda function to generate metrics
aws lambda invoke \
  --function-name co2-analysis-dev-reasoning-function \
  --payload '{"body": "{\"lat\":35.6762,\"lon\":139.6503,\"co2\":420.5,\"deviation\":5.2,\"date\":\"2025-11-01\",\"severity\":\"medium\",\"zscore\":2.1}"}' \
  response.json

# Wait 5 minutes, then check metrics
aws cloudwatch get-metric-statistics \
  --namespace co2-analysis/dev \
  --metric-name CacheHit \
  --start-time 2025-11-01T00:00:00Z \
  --end-time 2025-11-01T23:59:59Z \
  --period 300 \
  --statistics Sum
```

## Security

### CDK Nag Compliance
The stack includes CDK Nag suppressions for:
- **AwsSolutions-SNS2**: SNS topic encryption (not required for alarms)
- **AwsSolutions-SNS3**: SNS SSL enforcement (handled by enforceSSL property)

### Least Privilege
- CloudWatch Logs: Write-only permissions for Lambda
- SNS Topic: Publish-only permissions for CloudWatch Alarms
- Parameter Store: Read-only access for cross-stack references

### Data Protection
- All CloudWatch Logs encrypted at rest (AWS-managed keys)
- SNS messages transmitted over TLS
- No sensitive data in alarm messages or dashboard widgets

## Maintenance

### Regular Tasks
- Review alarm thresholds monthly
- Update email subscribers as team changes
- Archive old log groups (automated via retention settings)
- Review dashboard widgets for relevance

### Quarterly Reviews
- Analyze cost trends
- Review alarm history and tune thresholds
- Update documentation with lessons learned
- Optimize metric filters for new log patterns

## Related Documentation
- [AWS CloudWatch Documentation](https://docs.aws.amazon.com/cloudwatch/)
- [CDK CloudWatch Constructs](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cloudwatch-readme.html)
- [Parameter Store Integration Guide](./PARAMETER_STORE_INTEGRATION.md)
- [Main README](./README.md)

## Support

For issues or questions:
1. Check CloudWatch Logs for error messages
2. Review alarm history in CloudWatch Console
3. Consult this documentation
4. Contact DevOps team
