import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import { Construct } from 'constructs';
import { EnvironmentConfig } from '../config/environment';

export interface ComputeStackProps extends cdk.StackProps {
  lambdaExecutionRole: iam.IRole;
  cacheTable: dynamodb.ITable;
  geminiApiKeySecret: secretsmanager.ISecret;
}

/**
 * ComputeStack - Compute Layer (STUB)
 *
 * TODO: Implement full ComputeStack functionality
 * This is a stub implementation to allow MonitoringStack compilation
 */
export class ComputeStack extends cdk.Stack {
  public readonly reasoningFunction: lambda.IFunction;

  constructor(scope: Construct, id: string, config: EnvironmentConfig, props: ComputeStackProps) {
    super(scope, id, props);

    // Stub implementation - to be replaced with actual implementation
    this.reasoningFunction = {} as lambda.IFunction;
  }
}
