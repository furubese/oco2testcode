import * as cdk from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import { Construct } from 'constructs';
import { EnvironmentConfig } from '../config/environment';

/**
 * BaseStack - Foundation Layer (STUB)
 *
 * TODO: Implement full BaseStack functionality
 * This is a stub implementation to allow MonitoringStack compilation
 */
export class BaseStack extends cdk.Stack {
  public readonly lambdaExecutionRole: iam.IRole;
  public readonly geminiApiKeySecret: secretsmanager.ISecret;

  constructor(scope: Construct, id: string, config: EnvironmentConfig, props?: cdk.StackProps) {
    super(scope, id, props);

    // Stub implementation - to be replaced with actual implementation
    this.lambdaExecutionRole = {} as iam.IRole;
    this.geminiApiKeySecret = {} as secretsmanager.ISecret;
  }
}
