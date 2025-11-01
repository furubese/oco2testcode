/**
 * BaseStack - Foundation Layer (STUB)
 *
 * This is a stub implementation for dependency resolution.
 * Full implementation should be completed in a separate task.
 *
 * This stack should create:
 * - IAM roles for Lambda execution
 * - Secrets Manager secret for Gemini API key
 * - Base parameters
 */

import * as cdk from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import { Construct } from 'constructs';
import { EnvironmentConfig, getResourceName, getResourceTags } from '../config/environment';

export class BaseStack extends cdk.Stack {
  public readonly lambdaExecutionRole: iam.Role;
  public readonly geminiApiKeySecret: secretsmanager.Secret;

  constructor(scope: Construct, id: string, config: EnvironmentConfig, props?: cdk.StackProps) {
    super(scope, id, props);

    // Apply resource tags
    const tags = getResourceTags(config);
    Object.entries(tags).forEach(([key, value]) => {
      cdk.Tags.of(this).add(key, value);
    });

    // Lambda Execution Role with necessary permissions
    this.lambdaExecutionRole = new iam.Role(this, 'LambdaExecutionRole', {
      roleName: getResourceName(config, 'lambda-execution-role'),
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      description: 'Execution role for Lambda functions with DynamoDB and Secrets Manager access',
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
      ],
    });

    // Grant access to Secrets Manager for Gemini API key
    this.lambdaExecutionRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ['secretsmanager:GetSecretValue'],
        resources: [`arn:aws:secretsmanager:${cdk.Stack.of(this).region}:${cdk.Stack.of(this).account}:secret:${config.projectName}-${config.environment}-gemini-api-key-*`],
      })
    );

    // Grant access to Parameter Store for reading configuration
    this.lambdaExecutionRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ['ssm:GetParameter', 'ssm:GetParameters', 'ssm:GetParametersByPath'],
        resources: [`arn:aws:ssm:${cdk.Stack.of(this).region}:${cdk.Stack.of(this).account}:parameter/${config.projectName}/${config.environment}/*`],
      })
    );

    // Gemini API Key Secret
    this.geminiApiKeySecret = new secretsmanager.Secret(this, 'GeminiApiKeySecret', {
      secretName: getResourceName(config, 'gemini-api-key'),
      description: 'Google Gemini API key for AI reasoning',
      generateSecretString: {
        secretStringTemplate: JSON.stringify({ apiKey: 'PLACEHOLDER' }),
        generateStringKey: 'password',
      },
    });

    // Output for manual secret update
    new cdk.CfnOutput(this, 'GeminiApiKeySecretArn', {
      value: this.geminiApiKeySecret.secretArn,
      description: 'Update this secret with your Gemini API key',
      exportName: getResourceName(config, 'gemini-secret-arn'),
    });
  }
}
