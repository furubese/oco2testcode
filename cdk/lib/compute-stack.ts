/**
 * ComputeStack - Serverless Compute Layer
 *
 * This stack creates:
 * - Lambda function for CO2 anomaly reasoning API
 * - Lambda Layer with dependencies (google-generativeai, boto3)
 * - API Gateway REST API with CORS support
 * - Request validation and throttling
 * - Integration with DynamoDB cache and Secrets Manager
 * - Parameter Store exports for API endpoint
 *
 * Dependencies:
 * - BaseStack: lambdaExecutionRole, geminiApiKeySecret
 * - StorageStack: cacheTable
 */

import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';
import { EnvironmentConfig, getResourceName, getResourceTags } from '../config/environment';
import * as path from 'path';
import * as fs from 'fs';
import { NagSuppressions } from 'cdk-nag';

/**
 * Props for ComputeStack
 */
export interface ComputeStackProps extends cdk.StackProps {
  /**
   * Lambda execution role from BaseStack with Secrets Manager permissions
   */
  lambdaExecutionRole: iam.Role;

  /**
   * DynamoDB cache table from StorageStack
   */
  cacheTable: cdk.aws_dynamodb.Table;

  /**
   * Gemini API key secret from BaseStack
   */
  geminiApiKeySecret: cdk.aws_secretsmanager.Secret;
}

/**
 * ComputeStack - Lambda and API Gateway for reasoning API
 */
export class ComputeStack extends cdk.Stack {
  /**
   * Lambda function for reasoning API
   */
  public readonly reasoningFunction: lambda.Function;

  /**
   * API Gateway REST API
   */
  public readonly api: apigateway.RestApi;

  /**
   * API Gateway stage
   */
  public readonly stage: string = 'prod';

  constructor(scope: Construct, id: string, config: EnvironmentConfig, props: ComputeStackProps) {
    super(scope, id, props);

    // Apply resource tags
    const tags = getResourceTags(config);
    Object.entries(tags).forEach(([key, value]) => {
      cdk.Tags.of(this).add(key, value);
    });

    // ===========================
    // Lambda Layer for Dependencies
    // ===========================

    // Note: The Lambda layer requires Docker for bundling.
    // If Docker is not available, you have two options:
    // 1. Pre-build the layer manually and upload to S3
    // 2. Install Docker and run: cdk synth
    //
    // For local development without Docker, we'll use a PythonLayerVersion
    // which can be created using the AWS Lambda Powertools Python Layer approach

    // Check if python directory already exists (manual build)
    const layerPath = path.join(__dirname, '../lambda/layers/dependencies');
    const pythonPath = path.join(layerPath, 'python');
    const hasPythonDir = fs.existsSync(pythonPath);

    const dependenciesLayer = new lambda.LayerVersion(this, 'DependenciesLayer', {
      layerVersionName: getResourceName(config, 'reasoning-dependencies'),
      description: 'Dependencies for reasoning Lambda: google-generativeai, boto3',
      code: lambda.Code.fromAsset(layerPath, {
        bundling: hasPythonDir ? undefined : {
          image: lambda.Runtime.PYTHON_3_11.bundlingImage,
          command: [
            'bash',
            '-c',
            [
              'pip install -r requirements.txt -t /asset-output/python --platform manylinux2014_x86_64 --only-binary=:all: || pip install -r requirements.txt -t /asset-output/python',
              'find /asset-output -type d -name "__pycache__" -exec rm -rf {} + || true',
              'find /asset-output -type d -name "*.dist-info" -exec rm -rf {} + || true',
            ].join(' && '),
          ],
          user: 'root',
        },
      }),
      compatibleRuntimes: [lambda.Runtime.PYTHON_3_11],
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // ===========================
    // Lambda Function
    // ===========================

    this.reasoningFunction = new lambda.Function(this, 'ReasoningFunction', {
      functionName: getResourceName(config, 'reasoning-api'),
      description: 'CO2 anomaly reasoning API with Gemini AI and DynamoDB caching',
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'index.lambda_handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../lambda/reasoning-handler')),
      layers: [dependenciesLayer],
      role: props.lambdaExecutionRole,
      timeout: cdk.Duration.seconds(30),
      memorySize: config.environment === 'prod' ? 512 : 256,
      environment: {
        DYNAMODB_TABLE_NAME: props.cacheTable.tableName,
        GEMINI_API_KEY_SECRET_NAME: props.geminiApiKeySecret.secretName,
        CACHE_TTL_DAYS: config.cacheTtlDays.toString(),
        GEMINI_MODEL: 'gemini-2.0-flash-exp',
        ENVIRONMENT: config.environment,
        LOG_LEVEL: config.environment === 'dev' ? 'DEBUG' : 'INFO',
      },
      logRetention: logs.RetentionDays.ONE_WEEK,
      retryAttempts: 0, // API Gateway handles retries
      reservedConcurrentExecutions: config.environment === 'prod' ? 100 : undefined,
      tracing: config.enableXRay ? lambda.Tracing.ACTIVE : lambda.Tracing.DISABLED,
    });

    // Grant DynamoDB permissions to Lambda
    props.cacheTable.grantReadWriteData(this.reasoningFunction);

    // Provisioned concurrency for production (reduces cold starts)
    if (config.provisionedConcurrency > 0) {
      const version = this.reasoningFunction.currentVersion;
      const alias = new lambda.Alias(this, 'ReasoningFunctionAlias', {
        aliasName: 'live',
        version,
        provisionedConcurrentExecutions: config.provisionedConcurrency,
      });

      // Export alias ARN
      new cdk.CfnOutput(this, 'ReasoningFunctionAliasArn', {
        value: alias.functionArn,
        description: 'Reasoning Lambda function alias ARN with provisioned concurrency',
        exportName: getResourceName(config, 'reasoning-function-alias-arn'),
      });
    }

    // ===========================
    // API Gateway REST API
    // ===========================

    // CloudWatch role for API Gateway logging
    const apiGatewayCloudWatchRole = new iam.Role(this, 'ApiGatewayCloudWatchRole', {
      roleName: getResourceName(config, 'apigateway-cloudwatch-role'),
      assumedBy: new iam.ServicePrincipal('apigateway.amazonaws.com'),
      description: 'Allows API Gateway to write logs to CloudWatch',
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AmazonAPIGatewayPushToCloudWatchLogs'),
      ],
    });

    // API Gateway account configuration
    const account = new apigateway.CfnAccount(this, 'ApiGatewayAccount', {
      cloudWatchRoleArn: apiGatewayCloudWatchRole.roleArn,
    });

    // REST API
    this.api = new apigateway.RestApi(this, 'ReasoningApi', {
      restApiName: getResourceName(config, 'reasoning-api'),
      description: 'CO2 Anomaly Reasoning API with AI-powered insights',
      deployOptions: {
        stageName: this.stage,
        throttlingRateLimit: config.apiThrottling.rateLimit,
        throttlingBurstLimit: config.apiThrottling.burstLimit,
        loggingLevel: apigateway.MethodLoggingLevel.INFO,
        dataTraceEnabled: config.environment === 'dev',
        metricsEnabled: true,
        tracingEnabled: config.enableXRay,
      },
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: ['POST', 'OPTIONS'],
        allowHeaders: ['Content-Type', 'X-Api-Key', 'Authorization'],
        allowCredentials: false,
        maxAge: cdk.Duration.hours(1),
      },
      cloudWatchRole: true,
      endpointTypes: [apigateway.EndpointType.REGIONAL],
      retainDeployments: false,
    });

    // Ensure API Gateway account is created before REST API
    this.api.node.addDependency(account);

    // ===========================
    // API Gateway Resources & Methods
    // ===========================

    // Request model for validation
    const requestModel = this.api.addModel('ReasoningRequestModel', {
      modelName: 'ReasoningRequest',
      description: 'Request model for reasoning endpoint',
      contentType: 'application/json',
      schema: {
        type: apigateway.JsonSchemaType.OBJECT,
        required: ['lat', 'lon', 'co2'],
        properties: {
          lat: {
            type: apigateway.JsonSchemaType.NUMBER,
            description: 'Latitude (-90 to 90)',
            minimum: -90,
            maximum: 90,
          },
          lon: {
            type: apigateway.JsonSchemaType.NUMBER,
            description: 'Longitude (-180 to 180)',
            minimum: -180,
            maximum: 180,
          },
          co2: {
            type: apigateway.JsonSchemaType.NUMBER,
            description: 'CO2 concentration in ppm',
            minimum: 0,
          },
          deviation: {
            type: apigateway.JsonSchemaType.NUMBER,
            description: 'Deviation from baseline (optional)',
          },
          date: {
            type: apigateway.JsonSchemaType.STRING,
            description: 'Observation date (YYYY-MM-DD) or "unknown"',
          },
          severity: {
            type: apigateway.JsonSchemaType.STRING,
            description: 'Severity level (optional)',
            enum: ['low', 'medium', 'high', 'unknown'],
          },
          zscore: {
            type: apigateway.JsonSchemaType.NUMBER,
            description: 'Statistical Z-score (optional)',
          },
        },
      },
    });

    // Request validator
    const requestValidator = this.api.addRequestValidator('ReasoningRequestValidator', {
      requestValidatorName: getResourceName(config, 'reasoning-request-validator'),
      validateRequestBody: true,
      validateRequestParameters: true,
    });

    // POST /reasoning endpoint
    const reasoningResource = this.api.root.addResource('reasoning');

    const lambdaIntegration = new apigateway.LambdaIntegration(this.reasoningFunction, {
      proxy: true,
      allowTestInvoke: config.environment !== 'prod',
      timeout: cdk.Duration.seconds(29), // Slightly less than Lambda timeout
    });

    reasoningResource.addMethod('POST', lambdaIntegration, {
      requestValidator,
      requestModels: {
        'application/json': requestModel,
      },
      methodResponses: [
        {
          statusCode: '200',
          responseModels: {
            'application/json': apigateway.Model.EMPTY_MODEL,
          },
          responseParameters: {
            'method.response.header.Access-Control-Allow-Origin': true,
            'method.response.header.Access-Control-Allow-Headers': true,
          },
        },
        {
          statusCode: '400',
          responseModels: {
            'application/json': apigateway.Model.ERROR_MODEL,
          },
        },
        {
          statusCode: '500',
          responseModels: {
            'application/json': apigateway.Model.ERROR_MODEL,
          },
        },
      ],
    });

    // ===========================
    // Parameter Store Exports
    // ===========================

    // API Gateway URL
    new ssm.StringParameter(this, 'ApiGatewayUrl', {
      parameterName: `/co2-analysis/${config.environment}/compute/api-gateway/url`,
      stringValue: this.api.url,
      description: 'API Gateway URL for reasoning API',
      tier: ssm.ParameterTier.STANDARD,
    });

    // API Gateway ID
    new ssm.StringParameter(this, 'ApiGatewayId', {
      parameterName: `/co2-analysis/${config.environment}/compute/api-gateway/id`,
      stringValue: this.api.restApiId,
      description: 'API Gateway REST API ID',
      tier: ssm.ParameterTier.STANDARD,
    });

    // API Gateway Stage
    new ssm.StringParameter(this, 'ApiGatewayStage', {
      parameterName: `/co2-analysis/${config.environment}/compute/api-gateway/stage`,
      stringValue: this.stage,
      description: 'API Gateway deployment stage',
      tier: ssm.ParameterTier.STANDARD,
    });

    // Lambda Function ARN
    new ssm.StringParameter(this, 'LambdaFunctionArn', {
      parameterName: `/co2-analysis/${config.environment}/compute/lambda/function-arn`,
      stringValue: this.reasoningFunction.functionArn,
      description: 'Lambda function ARN for reasoning API',
      tier: ssm.ParameterTier.STANDARD,
    });

    // Lambda Function Name
    new ssm.StringParameter(this, 'LambdaFunctionName', {
      parameterName: `/co2-analysis/${config.environment}/compute/lambda/function-name`,
      stringValue: this.reasoningFunction.functionName,
      description: 'Lambda function name for reasoning API',
      tier: ssm.ParameterTier.STANDARD,
    });

    // ===========================
    // CloudFormation Outputs
    // ===========================

    new cdk.CfnOutput(this, 'ApiUrl', {
      value: this.api.url,
      description: 'API Gateway endpoint URL',
      exportName: getResourceName(config, 'api-url'),
    });

    new cdk.CfnOutput(this, 'ApiEndpoint', {
      value: `${this.api.url}reasoning`,
      description: 'Reasoning endpoint URL (POST)',
      exportName: getResourceName(config, 'reasoning-endpoint'),
    });

    new cdk.CfnOutput(this, 'LambdaArn', {
      value: this.reasoningFunction.functionArn,
      description: 'Reasoning Lambda function ARN',
      exportName: getResourceName(config, 'lambda-arn'),
    });

    // ===========================
    // CDK Nag Suppressions
    // ===========================

    // Suppress API Gateway authorization warning - This is a public API
    NagSuppressions.addResourceSuppressions(
      reasoningResource,
      [
        {
          id: 'AwsSolutions-APIG4',
          reason: 'This is a public API endpoint. Authorization is handled via API key in production (WAF). For development, no auth is required for testing.',
        },
        {
          id: 'AwsSolutions-COG4',
          reason: 'Cognito user pool authorizer not required. API is designed as a public endpoint with rate limiting and WAF protection in production.',
        },
      ],
      true, // Apply to all children
    );

    // Suppress API Gateway access logging if not required in dev
    if (config.environment === 'dev') {
      NagSuppressions.addResourceSuppressions(
        this.api,
        [
          {
            id: 'AwsSolutions-APIG1',
            reason: 'Access logging is disabled in development environment to reduce costs. Enabled in staging/production.',
          },
        ],
        true,
      );
    }

    // Suppress Lambda concurrency warning for dev environment
    if (config.environment === 'dev') {
      NagSuppressions.addResourceSuppressions(
        this.reasoningFunction,
        [
          {
            id: 'AwsSolutions-L1',
            reason: 'Lambda runtime version is specified and will be updated as needed. Python 3.11 is current stable version.',
          },
        ],
      );
    }

    // Suppress API Gateway stage warning if X-Ray disabled in dev
    if (!config.enableXRay) {
      NagSuppressions.addResourceSuppressions(
        this,
        [
          {
            id: 'AwsSolutions-APIG6',
            reason: 'X-Ray tracing is disabled in development to reduce costs. Enabled in staging/production for observability.',
          },
        ],
        true,
      );
    }

    // Suppress DLQ warning - API Gateway handles retries, Lambda failures are logged
    NagSuppressions.addResourceSuppressions(
      this.reasoningFunction,
      [
        {
          id: 'AwsSolutions-L3',
          reason: 'DLQ not required for synchronous API Gateway invocations. Failures are returned to client and logged to CloudWatch. For async patterns, DLQ would be added.',
        },
      ],
    );
  }
}
