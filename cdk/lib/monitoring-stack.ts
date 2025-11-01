import * as cdk from 'aws-cdk-lib';
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import * as cloudwatch_actions from 'aws-cdk-lib/aws-cloudwatch-actions';
import * as sns from 'aws-cdk-lib/aws-sns';
import * as sns_subscriptions from 'aws-cdk-lib/aws-sns-subscriptions';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { Construct } from 'constructs';
import { EnvironmentConfig, getResourceName, getResourceTags } from '../config/environment';
import { NagSuppressions } from 'cdk-nag';

/**
 * MonitoringStack Properties
 */
export interface MonitoringStackProps extends cdk.StackProps {
  reasoningFunction: lambda.IFunction;
  cacheTable: dynamodb.ITable;
  apiGateway?: any; // Will be added when ApiStack is implemented
}

/**
 * MonitoringStack - CloudWatch Observability Layer
 *
 * This stack implements comprehensive monitoring and observability using CloudWatch:
 * - CloudWatch Logs for Lambda functions with configurable retention
 * - Custom metrics for API calls, cache hit/miss ratio, Lambda duration, error rate
 * - CloudWatch alarms for error rate >5% and Lambda duration >10 seconds
 * - SNS topic for alarm notifications
 * - CloudWatch dashboard displaying system health metrics
 *
 * Layer 6: Observability (depends on ComputeStack, StorageStack)
 */
export class MonitoringStack extends cdk.Stack {
  public readonly alarmTopic: sns.Topic;
  public readonly dashboard: cloudwatch.Dashboard;

  constructor(scope: Construct, id: string, config: EnvironmentConfig, props: MonitoringStackProps) {
    super(scope, id, props);

    const { reasoningFunction, cacheTable } = props;

    // ========================================
    // SNS Topic for Alarm Notifications
    // ========================================

    this.alarmTopic = new sns.Topic(this, 'AlarmTopic', {
      topicName: getResourceName(config, 'alarm-topic'),
      displayName: `${config.appName} - ${config.environment} Alarms`,
      enforceSSL: true,
    });

    // Add email subscription if configured
    if (config.alarmEmail) {
      this.alarmTopic.addSubscription(
        new sns_subscriptions.EmailSubscription(config.alarmEmail)
      );
    }

    // Export SNS topic ARN to Parameter Store
    new ssm.StringParameter(this, 'AlarmTopicArnParameter', {
      parameterName: `/co2-analysis/${config.environment}/monitoring/sns/alarm-topic-arn`,
      stringValue: this.alarmTopic.topicArn,
      description: 'SNS topic ARN for CloudWatch alarm notifications',
      tier: ssm.ParameterTier.STANDARD,
    });

    // ========================================
    // CloudWatch Logs Configuration
    // ========================================

    // Lambda function log group (created automatically, but we configure retention)
    const lambdaLogGroup = new logs.LogGroup(this, 'ReasoningFunctionLogGroup', {
      logGroupName: `/aws/lambda/${reasoningFunction.functionName}`,
      retention: this.getLogRetention(config.logRetentionDays),
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // ========================================
    // Custom Metrics and Metric Filters
    // ========================================

    // Metric namespace
    const metricNamespace = `${config.projectName}/${config.environment}`;

    // 1. Cache Hit Metric Filter
    const cacheHitMetricFilter = new logs.MetricFilter(this, 'CacheHitMetricFilter', {
      logGroup: lambdaLogGroup,
      metricNamespace,
      metricName: 'CacheHit',
      filterPattern: logs.FilterPattern.literal('[...] Cache HIT for key:'),
      metricValue: '1',
      defaultValue: 0,
    });

    // 2. Cache Miss Metric Filter
    const cacheMissMetricFilter = new logs.MetricFilter(this, 'CacheMissMetricFilter', {
      logGroup: lambdaLogGroup,
      metricNamespace,
      metricName: 'CacheMiss',
      filterPattern: logs.FilterPattern.literal('[...] Cache MISS for key:'),
      metricValue: '1',
      defaultValue: 0,
    });

    // 3. API Call Metric Filter (Gemini API calls)
    const apiCallMetricFilter = new logs.MetricFilter(this, 'ApiCallMetricFilter', {
      logGroup: lambdaLogGroup,
      metricNamespace,
      metricName: 'GeminiApiCalls',
      filterPattern: logs.FilterPattern.literal('[...] Generated reasoning for'),
      metricValue: '1',
      defaultValue: 0,
    });

    // 4. Error Metric Filter
    const errorMetricFilter = new logs.MetricFilter(this, 'ErrorMetricFilter', {
      logGroup: lambdaLogGroup,
      metricNamespace,
      metricName: 'Errors',
      filterPattern: logs.FilterPattern.anyTerm('ERROR', 'Error', 'Exception', 'Failed'),
      metricValue: '1',
      defaultValue: 0,
    });

    // ========================================
    // CloudWatch Metrics - Lambda Function
    // ========================================

    // Lambda Errors metric
    const lambdaErrorsMetric = reasoningFunction.metricErrors({
      statistic: cloudwatch.Stats.SUM,
      period: cdk.Duration.minutes(5),
    });

    // Lambda Duration metric
    const lambdaDurationMetric = reasoningFunction.metricDuration({
      statistic: cloudwatch.Stats.AVERAGE,
      period: cdk.Duration.minutes(1),
    });

    // Lambda Invocations metric
    const lambdaInvocationsMetric = reasoningFunction.metricInvocations({
      statistic: cloudwatch.Stats.SUM,
      period: cdk.Duration.minutes(5),
    });

    // Lambda Throttles metric
    const lambdaThrottlesMetric = reasoningFunction.metricThrottles({
      statistic: cloudwatch.Stats.SUM,
      period: cdk.Duration.minutes(5),
    });

    // ========================================
    // CloudWatch Metrics - DynamoDB
    // ========================================

    // DynamoDB Read Throttles
    const dynamoReadThrottlesMetric = cacheTable.metricUserErrors({
      statistic: cloudwatch.Stats.SUM,
      period: cdk.Duration.minutes(5),
    });

    // DynamoDB Consumed Read Capacity
    const dynamoConsumedReadCapacityMetric = cacheTable.metricConsumedReadCapacityUnits({
      statistic: cloudwatch.Stats.SUM,
      period: cdk.Duration.minutes(5),
    });

    // DynamoDB Consumed Write Capacity
    const dynamoConsumedWriteCapacityMetric = cacheTable.metricConsumedWriteCapacityUnits({
      statistic: cloudwatch.Stats.SUM,
      period: cdk.Duration.minutes(5),
    });

    // ========================================
    // Custom Metrics - Cache Hit/Miss Ratio
    // ========================================

    const cacheHitMetric = new cloudwatch.Metric({
      namespace: metricNamespace,
      metricName: 'CacheHit',
      statistic: cloudwatch.Stats.SUM,
      period: cdk.Duration.minutes(5),
    });

    const cacheMissMetric = new cloudwatch.Metric({
      namespace: metricNamespace,
      metricName: 'CacheMiss',
      statistic: cloudwatch.Stats.SUM,
      period: cdk.Duration.minutes(5),
    });

    const geminiApiCallsMetric = new cloudwatch.Metric({
      namespace: metricNamespace,
      metricName: 'GeminiApiCalls',
      statistic: cloudwatch.Stats.SUM,
      period: cdk.Duration.minutes(5),
    });

    const customErrorsMetric = new cloudwatch.Metric({
      namespace: metricNamespace,
      metricName: 'Errors',
      statistic: cloudwatch.Stats.SUM,
      period: cdk.Duration.minutes(5),
    });

    // Calculate cache hit ratio (using math expression)
    const cacheHitRatioMetric = new cloudwatch.MathExpression({
      expression: '(cacheHit / (cacheHit + cacheMiss)) * 100',
      usingMetrics: {
        cacheHit: cacheHitMetric,
        cacheMiss: cacheMissMetric,
      },
      period: cdk.Duration.minutes(5),
      label: 'Cache Hit Ratio (%)',
    });

    // Calculate error rate (using math expression)
    const errorRateMetric = new cloudwatch.MathExpression({
      expression: '(errors / invocations) * 100',
      usingMetrics: {
        errors: lambdaErrorsMetric,
        invocations: lambdaInvocationsMetric,
      },
      period: cdk.Duration.minutes(5),
      label: 'Error Rate (%)',
    });

    // ========================================
    // CloudWatch Alarms
    // ========================================

    // 1. Lambda Error Rate Alarm (>5%)
    const errorRateAlarm = new cloudwatch.Alarm(this, 'ErrorRateAlarm', {
      alarmName: getResourceName(config, 'error-rate-high'),
      alarmDescription: 'Alert when Lambda error rate exceeds 5%',
      metric: errorRateMetric,
      threshold: 5,
      evaluationPeriods: 2,
      datapointsToAlarm: 2,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });
    errorRateAlarm.addAlarmAction(new cloudwatch_actions.SnsAction(this.alarmTopic));

    // 2. Lambda Duration Alarm (>10 seconds)
    const durationAlarm = new cloudwatch.Alarm(this, 'DurationAlarm', {
      alarmName: getResourceName(config, 'lambda-duration-high'),
      alarmDescription: 'Alert when Lambda duration exceeds 10 seconds',
      metric: lambdaDurationMetric,
      threshold: 10000, // 10 seconds in milliseconds
      evaluationPeriods: 2,
      datapointsToAlarm: 2,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });
    durationAlarm.addAlarmAction(new cloudwatch_actions.SnsAction(this.alarmTopic));

    // 3. Lambda Errors Alarm (absolute count)
    const lambdaErrorsAlarm = new cloudwatch.Alarm(this, 'LambdaErrorsAlarm', {
      alarmName: getResourceName(config, 'lambda-errors'),
      alarmDescription: 'Alert when Lambda errors exceed 5 in 5 minutes',
      metric: lambdaErrorsMetric,
      threshold: 5,
      evaluationPeriods: 1,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });
    lambdaErrorsAlarm.addAlarmAction(new cloudwatch_actions.SnsAction(this.alarmTopic));

    // 4. Lambda Throttles Alarm
    const throttlesAlarm = new cloudwatch.Alarm(this, 'ThrottlesAlarm', {
      alarmName: getResourceName(config, 'lambda-throttles'),
      alarmDescription: 'Alert when Lambda throttles occur',
      metric: lambdaThrottlesMetric,
      threshold: 1,
      evaluationPeriods: 1,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });
    throttlesAlarm.addAlarmAction(new cloudwatch_actions.SnsAction(this.alarmTopic));

    // 5. DynamoDB Throttles Alarm
    const dynamoThrottlesAlarm = new cloudwatch.Alarm(this, 'DynamoThrottlesAlarm', {
      alarmName: getResourceName(config, 'dynamodb-throttles'),
      alarmDescription: 'Alert when DynamoDB throttles exceed 10 in 5 minutes',
      metric: dynamoReadThrottlesMetric,
      threshold: 10,
      evaluationPeriods: 1,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });
    dynamoThrottlesAlarm.addAlarmAction(new cloudwatch_actions.SnsAction(this.alarmTopic));

    // 6. Cache Hit Ratio Alarm (low cache efficiency)
    const cacheHitRatioAlarm = new cloudwatch.Alarm(this, 'CacheHitRatioAlarm', {
      alarmName: getResourceName(config, 'cache-hit-ratio-low'),
      alarmDescription: 'Alert when cache hit ratio falls below 50%',
      metric: cacheHitRatioMetric,
      threshold: 50,
      evaluationPeriods: 3,
      datapointsToAlarm: 2,
      comparisonOperator: cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });
    cacheHitRatioAlarm.addAlarmAction(new cloudwatch_actions.SnsAction(this.alarmTopic));

    // ========================================
    // CloudWatch Dashboard
    // ========================================

    this.dashboard = new cloudwatch.Dashboard(this, 'OperationalDashboard', {
      dashboardName: getResourceName(config, 'operational-dashboard'),
    });

    // Export dashboard name to Parameter Store
    new ssm.StringParameter(this, 'DashboardNameParameter', {
      parameterName: `/co2-analysis/${config.environment}/monitoring/cloudwatch/dashboard-name`,
      stringValue: this.dashboard.dashboardName,
      description: 'CloudWatch dashboard name for operational metrics',
      tier: ssm.ParameterTier.STANDARD,
    });

    // Dashboard Row 1: Lambda Performance
    this.dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: 'Lambda Invocations',
        left: [lambdaInvocationsMetric],
        width: 8,
        height: 6,
      }),
      new cloudwatch.GraphWidget({
        title: 'Lambda Duration (ms)',
        left: [lambdaDurationMetric],
        width: 8,
        height: 6,
        leftYAxis: {
          min: 0,
        },
      }),
      new cloudwatch.GraphWidget({
        title: 'Lambda Errors & Throttles',
        left: [lambdaErrorsMetric, lambdaThrottlesMetric],
        width: 8,
        height: 6,
      })
    );

    // Dashboard Row 2: Error Rate and Cache Performance
    this.dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: 'Error Rate (%)',
        left: [errorRateMetric],
        width: 8,
        height: 6,
        leftYAxis: {
          min: 0,
          max: 100,
        },
      }),
      new cloudwatch.GraphWidget({
        title: 'Cache Hit/Miss',
        left: [cacheHitMetric, cacheMissMetric],
        width: 8,
        height: 6,
      }),
      new cloudwatch.GraphWidget({
        title: 'Cache Hit Ratio (%)',
        left: [cacheHitRatioMetric],
        width: 8,
        height: 6,
        leftYAxis: {
          min: 0,
          max: 100,
        },
      })
    );

    // Dashboard Row 3: DynamoDB Metrics
    this.dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: 'DynamoDB Consumed Capacity',
        left: [dynamoConsumedReadCapacityMetric],
        right: [dynamoConsumedWriteCapacityMetric],
        width: 12,
        height: 6,
      }),
      new cloudwatch.GraphWidget({
        title: 'DynamoDB Throttles',
        left: [dynamoReadThrottlesMetric],
        width: 12,
        height: 6,
      })
    );

    // Dashboard Row 4: API Calls and Custom Metrics
    this.dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: 'Gemini API Calls',
        left: [geminiApiCallsMetric],
        width: 12,
        height: 6,
      }),
      new cloudwatch.GraphWidget({
        title: 'Application Errors',
        left: [customErrorsMetric],
        width: 12,
        height: 6,
      })
    );

    // Dashboard Row 5: Alarm Status
    this.dashboard.addWidgets(
      new cloudwatch.AlarmStatusWidget({
        title: 'Alarm Status',
        alarms: [
          errorRateAlarm,
          durationAlarm,
          lambdaErrorsAlarm,
          throttlesAlarm,
          dynamoThrottlesAlarm,
          cacheHitRatioAlarm,
        ],
        width: 24,
        height: 6,
      })
    );

    // ========================================
    // Tags
    // ========================================

    const tags = getResourceTags(config);
    Object.entries(tags).forEach(([key, value]) => {
      cdk.Tags.of(this).add(key, value);
    });

    // ========================================
    // CDK Nag Suppressions
    // ========================================

    // SNS Topic - Suppress warnings about KMS encryption (not required for alarms)
    NagSuppressions.addResourceSuppressions(
      this.alarmTopic,
      [
        {
          id: 'AwsSolutions-SNS2',
          reason: 'SNS topic for CloudWatch alarms does not require KMS encryption for this use case',
        },
        {
          id: 'AwsSolutions-SNS3',
          reason: 'SNS topic for CloudWatch alarms does not require SSL in transit (handled by enforceSSL)',
        },
      ],
      true
    );

    // ========================================
    // Stack Outputs
    // ========================================

    new cdk.CfnOutput(this, 'AlarmTopicArn', {
      description: 'SNS Topic ARN for CloudWatch alarms',
      value: this.alarmTopic.topicArn,
      exportName: `${config.projectName}-${config.environment}-alarm-topic-arn`,
    });

    new cdk.CfnOutput(this, 'DashboardUrl', {
      description: 'CloudWatch Dashboard URL',
      value: `https://console.aws.amazon.com/cloudwatch/home?region=${this.region}#dashboards:name=${this.dashboard.dashboardName}`,
    });

    new cdk.CfnOutput(this, 'DashboardName', {
      description: 'CloudWatch Dashboard Name',
      value: this.dashboard.dashboardName,
      exportName: `${config.projectName}-${config.environment}-dashboard-name`,
    });
  }

  /**
   * Get CloudWatch Logs retention period based on days
   */
  private getLogRetention(days: number): logs.RetentionDays {
    const retentionMap: Record<number, logs.RetentionDays> = {
      1: logs.RetentionDays.ONE_DAY,
      3: logs.RetentionDays.THREE_DAYS,
      5: logs.RetentionDays.FIVE_DAYS,
      7: logs.RetentionDays.ONE_WEEK,
      14: logs.RetentionDays.TWO_WEEKS,
      30: logs.RetentionDays.ONE_MONTH,
      60: logs.RetentionDays.TWO_MONTHS,
      90: logs.RetentionDays.THREE_MONTHS,
      120: logs.RetentionDays.FOUR_MONTHS,
      150: logs.RetentionDays.FIVE_MONTHS,
      180: logs.RetentionDays.SIX_MONTHS,
      365: logs.RetentionDays.ONE_YEAR,
      400: logs.RetentionDays.THIRTEEN_MONTHS,
      545: logs.RetentionDays.EIGHTEEN_MONTHS,
      731: logs.RetentionDays.TWO_YEARS,
      1827: logs.RetentionDays.FIVE_YEARS,
      3653: logs.RetentionDays.TEN_YEARS,
    };

    return retentionMap[days] || logs.RetentionDays.ONE_WEEK;
  }
}
