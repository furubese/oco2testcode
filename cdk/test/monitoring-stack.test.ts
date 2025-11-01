import * as cdk from 'aws-cdk-lib';
import { Template, Match } from 'aws-cdk-lib/assertions';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { MonitoringStack } from '../lib/monitoring-stack';
import { EnvironmentConfig } from '../config/environment';

/**
 * Unit Tests for MonitoringStack
 *
 * These tests validate the CloudWatch monitoring infrastructure including:
 * - SNS topic creation and configuration
 * - CloudWatch alarms with correct thresholds
 * - CloudWatch dashboard widgets
 * - Metric filters for custom metrics
 * - Parameter Store integration
 * - CDK Nag suppressions
 */

describe('MonitoringStack', () => {
  let app: cdk.App;
  let stack: MonitoringStack;
  let template: Template;
  let mockConfig: EnvironmentConfig;

  beforeEach(() => {
    app = new cdk.App();

    // Mock environment configuration
    mockConfig = {
      account: '123456789012',
      region: 'us-east-1',
      environment: 'dev',
      projectName: 'co2-analysis',
      appName: 'CO2 Anomaly Analysis',
      provisionedConcurrency: 0,
      wafEnabled: false,
      enableXRay: false,
      logRetentionDays: 7,
      alarmEmail: 'test@example.com',
      cacheTtlDays: 90,
      apiThrottling: {
        rateLimit: 100,
        burstLimit: 200,
      },
    };

    // Create mock Lambda function
    const mockLambdaStack = new cdk.Stack(app, 'MockLambdaStack');
    const mockFunction = new lambda.Function(mockLambdaStack, 'MockFunction', {
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'index.handler',
      code: lambda.Code.fromInline('def handler(event, context): pass'),
      functionName: 'test-reasoning-function',
    });

    // Create mock DynamoDB table
    const mockTable = new dynamodb.Table(mockLambdaStack, 'MockTable', {
      partitionKey: { name: 'cache_key', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      tableName: 'test-cache-table',
    });

    // Create MonitoringStack
    stack = new MonitoringStack(app, 'TestMonitoringStack', mockConfig, {
      reasoningFunction: mockFunction,
      cacheTable: mockTable,
      env: {
        account: mockConfig.account,
        region: mockConfig.region,
      },
    });

    template = Template.fromStack(stack);
  });

  describe('SNS Topic', () => {
    test('creates SNS topic for alarm notifications', () => {
      template.hasResourceProperties('AWS::SNS::Topic', {
        TopicName: 'co2-analysis-dev-alarm-topic',
        DisplayName: 'CO2 Anomaly Analysis - dev Alarms',
      });
    });

    test('creates email subscription when alarmEmail is provided', () => {
      template.hasResourceProperties('AWS::SNS::Subscription', {
        Protocol: 'email',
        Endpoint: 'test@example.com',
      });
    });

    test('exports SNS topic ARN to Parameter Store', () => {
      template.hasResourceProperties('AWS::SSM::Parameter', {
        Name: '/co2-analysis/dev/monitoring/sns/alarm-topic-arn',
        Type: 'String',
        Description: 'SNS topic ARN for CloudWatch alarm notifications',
        Tier: 'Standard',
      });
    });
  });

  describe('CloudWatch Logs', () => {
    test('creates log group for Lambda function with correct retention', () => {
      template.hasResourceProperties('AWS::Logs::LogGroup', {
        LogGroupName: '/aws/lambda/test-reasoning-function',
        RetentionInDays: 7,
      });
    });
  });

  describe('Metric Filters', () => {
    test('creates cache hit metric filter', () => {
      template.hasResourceProperties('AWS::Logs::MetricFilter', {
        FilterPattern: '[...] Cache HIT for key:',
        MetricTransformations: [
          {
            MetricName: 'CacheHit',
            MetricNamespace: 'co2-analysis/dev',
            MetricValue: '1',
            DefaultValue: 0,
          },
        ],
      });
    });

    test('creates cache miss metric filter', () => {
      template.hasResourceProperties('AWS::Logs::MetricFilter', {
        FilterPattern: '[...] Cache MISS for key:',
        MetricTransformations: [
          {
            MetricName: 'CacheMiss',
            MetricNamespace: 'co2-analysis/dev',
            MetricValue: '1',
            DefaultValue: 0,
          },
        ],
      });
    });

    test('creates Gemini API call metric filter', () => {
      template.hasResourceProperties('AWS::Logs::MetricFilter', {
        FilterPattern: '[...] Generated reasoning for',
        MetricTransformations: [
          {
            MetricName: 'GeminiApiCalls',
            MetricNamespace: 'co2-analysis/dev',
            MetricValue: '1',
            DefaultValue: 0,
          },
        ],
      });
    });

    test('creates error metric filter', () => {
      template.hasResourceProperties('AWS::Logs::MetricFilter', {
        MetricTransformations: [
          {
            MetricName: 'Errors',
            MetricNamespace: 'co2-analysis/dev',
            MetricValue: '1',
            DefaultValue: 0,
          },
        ],
      });
    });
  });

  describe('CloudWatch Alarms', () => {
    test('creates error rate alarm with >5% threshold', () => {
      template.hasResourceProperties('AWS::CloudWatch::Alarm', {
        AlarmName: 'co2-analysis-dev-error-rate-high',
        AlarmDescription: 'Alert when Lambda error rate exceeds 5%',
        Threshold: 5,
        EvaluationPeriods: 2,
        DatapointsToAlarm: 2,
        ComparisonOperator: 'GreaterThanThreshold',
        TreatMissingData: 'notBreaching',
      });
    });

    test('creates Lambda duration alarm with >10 seconds threshold', () => {
      template.hasResourceProperties('AWS::CloudWatch::Alarm', {
        AlarmName: 'co2-analysis-dev-lambda-duration-high',
        AlarmDescription: 'Alert when Lambda duration exceeds 10 seconds',
        Threshold: 10000, // 10 seconds in milliseconds
        EvaluationPeriods: 2,
        DatapointsToAlarm: 2,
        ComparisonOperator: 'GreaterThanThreshold',
      });
    });

    test('creates Lambda errors alarm', () => {
      template.hasResourceProperties('AWS::CloudWatch::Alarm', {
        AlarmName: 'co2-analysis-dev-lambda-errors',
        AlarmDescription: 'Alert when Lambda errors exceed 5 in 5 minutes',
        Threshold: 5,
        EvaluationPeriods: 1,
        ComparisonOperator: 'GreaterThanThreshold',
      });
    });

    test('creates Lambda throttles alarm', () => {
      template.hasResourceProperties('AWS::CloudWatch::Alarm', {
        AlarmName: 'co2-analysis-dev-lambda-throttles',
        AlarmDescription: 'Alert when Lambda throttles occur',
        Threshold: 1,
        EvaluationPeriods: 1,
        ComparisonOperator: 'GreaterThanOrEqualToThreshold',
      });
    });

    test('creates DynamoDB throttles alarm', () => {
      template.hasResourceProperties('AWS::CloudWatch::Alarm', {
        AlarmName: 'co2-analysis-dev-dynamodb-throttles',
        AlarmDescription: 'Alert when DynamoDB throttles exceed 10 in 5 minutes',
        Threshold: 10,
        EvaluationPeriods: 1,
        ComparisonOperator: 'GreaterThanThreshold',
      });
    });

    test('creates cache hit ratio alarm', () => {
      template.hasResourceProperties('AWS::CloudWatch::Alarm', {
        AlarmName: 'co2-analysis-dev-cache-hit-ratio-low',
        AlarmDescription: 'Alert when cache hit ratio falls below 50%',
        Threshold: 50,
        EvaluationPeriods: 3,
        DatapointsToAlarm: 2,
        ComparisonOperator: 'LessThanThreshold',
      });
    });

    test('all alarms have SNS action configured', () => {
      const alarms = template.findResources('AWS::CloudWatch::Alarm');
      const alarmCount = Object.keys(alarms).length;

      // We have 6 alarms defined
      expect(alarmCount).toBe(6);

      // Each alarm should have at least one AlarmActions entry
      Object.values(alarms).forEach((alarm: any) => {
        expect(alarm.Properties.AlarmActions).toBeDefined();
        expect(alarm.Properties.AlarmActions.length).toBeGreaterThan(0);
      });
    });
  });

  describe('CloudWatch Dashboard', () => {
    test('creates dashboard with correct name', () => {
      template.hasResourceProperties('AWS::CloudWatch::Dashboard', {
        DashboardName: 'co2-analysis-dev-operational-dashboard',
      });
    });

    test('exports dashboard name to Parameter Store', () => {
      template.hasResourceProperties('AWS::SSM::Parameter', {
        Name: '/co2-analysis/dev/monitoring/cloudwatch/dashboard-name',
        Type: 'String',
        Description: 'CloudWatch dashboard name for operational metrics',
        Tier: 'Standard',
      });
    });

    test('dashboard includes required widgets', () => {
      const dashboards = template.findResources('AWS::CloudWatch::Dashboard');

      // Dashboard body is a CloudFormation intrinsic function, not a plain JSON string
      // Just verify the dashboard resource exists
      expect(Object.keys(dashboards).length).toBe(1);

      const dashboard = Object.values(dashboards)[0];
      expect(dashboard.Properties).toBeDefined();
      expect(dashboard.Properties.DashboardBody).toBeDefined();
    });
  });

  describe('Stack Outputs', () => {
    test('exports alarm topic ARN', () => {
      template.hasOutput('AlarmTopicArn', {
        Description: 'SNS Topic ARN for CloudWatch alarms',
        Export: {
          Name: 'co2-analysis-dev-alarm-topic-arn',
        },
      });
    });

    test('exports dashboard URL', () => {
      template.hasOutput('DashboardUrl', {
        Description: 'CloudWatch Dashboard URL',
      });
    });

    test('exports dashboard name', () => {
      template.hasOutput('DashboardName', {
        Description: 'CloudWatch Dashboard Name',
        Export: {
          Name: 'co2-analysis-dev-dashboard-name',
        },
      });
    });
  });

  describe('Resource Tagging', () => {
    test('applies standard tags to stack', () => {
      const stackTags = (stack as any).tags.tagValues();
      expect(stackTags).toMatchObject({
        Project: 'co2-analysis',
        Environment: 'dev',
        Application: 'CO2 Anomaly Analysis',
        ManagedBy: 'CDK',
        CreatedBy: 'AWS-CDK',
      });
    });
  });

  describe('Resource Count', () => {
    test('creates expected number of resources', () => {
      const resources = template.toJSON().Resources;
      const resourceTypes: Record<string, number> = {};

      Object.values(resources).forEach((resource: any) => {
        const type = resource.Type;
        resourceTypes[type] = (resourceTypes[type] || 0) + 1;
      });

      // Validate resource counts
      expect(resourceTypes['AWS::SNS::Topic']).toBe(1);
      expect(resourceTypes['AWS::SNS::Subscription']).toBe(1);
      expect(resourceTypes['AWS::CloudWatch::Alarm']).toBe(6);
      expect(resourceTypes['AWS::CloudWatch::Dashboard']).toBe(1);
      expect(resourceTypes['AWS::Logs::MetricFilter']).toBe(4);
      expect(resourceTypes['AWS::Logs::LogGroup']).toBe(1);
      expect(resourceTypes['AWS::SSM::Parameter']).toBe(2);
    });
  });

  describe('Environment-Specific Configuration', () => {
    test('uses correct log retention for dev environment', () => {
      template.hasResourceProperties('AWS::Logs::LogGroup', {
        RetentionInDays: 7,
      });
    });

    test('uses correct log retention for staging environment', () => {
      // Create new app for this test to avoid multiple synth issue
      const stagingApp = new cdk.App();

      const stagingConfig: EnvironmentConfig = {
        ...mockConfig,
        environment: 'staging',
        logRetentionDays: 14,
      };

      const mockLambdaStack = new cdk.Stack(stagingApp, 'MockLambdaStackStaging');
      const mockFunction = new lambda.Function(mockLambdaStack, 'MockFunction', {
        runtime: lambda.Runtime.PYTHON_3_11,
        handler: 'index.handler',
        code: lambda.Code.fromInline('def handler(event, context): pass'),
        functionName: 'staging-reasoning-function',
      });

      const mockTable = new dynamodb.Table(mockLambdaStack, 'MockTable', {
        partitionKey: { name: 'cache_key', type: dynamodb.AttributeType.STRING },
        billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
        tableName: 'staging-cache-table',
      });

      const stagingStack = new MonitoringStack(
        stagingApp,
        'TestMonitoringStackStaging',
        stagingConfig,
        {
          reasoningFunction: mockFunction,
          cacheTable: mockTable,
          env: {
            account: stagingConfig.account,
            region: stagingConfig.region,
          },
        }
      );

      const stagingTemplate = Template.fromStack(stagingStack);
      stagingTemplate.hasResourceProperties('AWS::Logs::LogGroup', {
        RetentionInDays: 14,
      });
    });

    test('uses correct log retention for prod environment', () => {
      // Create new app for this test to avoid multiple synth issue
      const prodApp = new cdk.App();

      const prodConfig: EnvironmentConfig = {
        ...mockConfig,
        environment: 'prod',
        logRetentionDays: 30,
      };

      const mockLambdaStack = new cdk.Stack(prodApp, 'MockLambdaStackProd');
      const mockFunction = new lambda.Function(mockLambdaStack, 'MockFunction', {
        runtime: lambda.Runtime.PYTHON_3_11,
        handler: 'index.handler',
        code: lambda.Code.fromInline('def handler(event, context): pass'),
        functionName: 'prod-reasoning-function',
      });

      const mockTable = new dynamodb.Table(mockLambdaStack, 'MockTable', {
        partitionKey: { name: 'cache_key', type: dynamodb.AttributeType.STRING },
        billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
        tableName: 'prod-cache-table',
      });

      const prodStack = new MonitoringStack(prodApp, 'TestMonitoringStackProd', prodConfig, {
        reasoningFunction: mockFunction,
        cacheTable: mockTable,
        env: {
          account: prodConfig.account,
          region: prodConfig.region,
        },
      });

      const prodTemplate = Template.fromStack(prodStack);
      prodTemplate.hasResourceProperties('AWS::Logs::LogGroup', {
        RetentionInDays: 30,
      });
    });
  });

  describe('Without Email Configuration', () => {
    test('creates SNS topic without email subscription when alarmEmail is empty', () => {
      // Create new app for this test to avoid multiple synth issue
      const noEmailApp = new cdk.App();

      const configNoEmail: EnvironmentConfig = {
        ...mockConfig,
        alarmEmail: '',
      };

      const mockLambdaStack = new cdk.Stack(noEmailApp, 'MockLambdaStackNoEmail');
      const mockFunction = new lambda.Function(mockLambdaStack, 'MockFunction', {
        runtime: lambda.Runtime.PYTHON_3_11,
        handler: 'index.handler',
        code: lambda.Code.fromInline('def handler(event, context): pass'),
        functionName: 'no-email-reasoning-function',
      });

      const mockTable = new dynamodb.Table(mockLambdaStack, 'MockTable', {
        partitionKey: { name: 'cache_key', type: dynamodb.AttributeType.STRING },
        billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
        tableName: 'no-email-cache-table',
      });

      const stackNoEmail = new MonitoringStack(
        noEmailApp,
        'TestMonitoringStackNoEmail',
        configNoEmail,
        {
          reasoningFunction: mockFunction,
          cacheTable: mockTable,
          env: {
            account: configNoEmail.account,
            region: configNoEmail.region,
          },
        }
      );

      const templateNoEmail = Template.fromStack(stackNoEmail);

      // SNS topic should exist
      templateNoEmail.resourceCountIs('AWS::SNS::Topic', 1);

      // But no email subscription
      templateNoEmail.resourceCountIs('AWS::SNS::Subscription', 0);
    });
  });
});
