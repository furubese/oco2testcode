/**
 * BaseStack - Foundation Layer (STUB)
 *
 * This is a stub implementation for dependency resolution.
 * Full implementation should be completed in a separate task.
 *
 * This stack should create:
 * - IAM roles for Lambda execution with Bedrock permissions
 * - Base parameters
 */

import * as cdk from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';
import { EnvironmentConfig, getResourceName, getResourceTags } from '../config/environment';

export class BaseStack extends cdk.Stack {
  public readonly lambdaExecutionRole: iam.Role;

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
      description: 'Execution role for Lambda functions with DynamoDB and Bedrock access',
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
      ],
    });

    // Grant access to Bedrock for AI model invocation
    this.lambdaExecutionRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ['bedrock:InvokeModel'],
        resources: ['arn:aws:bedrock:us-east-1::foundation-model/us.amazon.nova-pro-v1:0'],
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
  }
}
