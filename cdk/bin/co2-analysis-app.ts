#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { BaseStack } from '../lib/base-stack';
import { NetworkStack } from '../lib/network-stack';
import { StorageStack } from '../lib/storage-stack';
import { ComputeStack } from '../lib/compute-stack';
import { FrontendStack } from '../lib/frontend-stack';
import { MonitoringStack } from '../lib/monitoring-stack';
import { getEnvironmentConfig } from '../config/environment';

/**
 * CO2 Anomaly Analysis System - CDK Application
 *
 * This application deploys a serverless architecture for analyzing CO2 anomalies
 * using AWS services and Google Gemini AI.
 *
 * Stack Deployment Order:
 * 1. BaseStack - IAM roles, secrets, parameters
 * 2. NetworkStack - VPC, security groups (optional)
 * 3. StorageStack - DynamoDB, S3 buckets
 * 4. ComputeStack - Lambda function and layer
 * 5. FrontendStack - CloudFront, static website
 * 6. MonitoringStack - CloudWatch, alarms, SNS
 *
 * Usage:
 *   cdk deploy --all --context environment=dev
 *   cdk deploy --all --context environment=staging
 *   cdk deploy --all --context environment=prod
 */

const app = new cdk.App();

// Get environment from context (defaults to 'dev')
const environmentName = app.node.tryGetContext('environment') || 'dev';

// Load environment configuration
const config = getEnvironmentConfig(app.node.tryGetContext(), environmentName);

// Validate required configuration
if (!config.account && !process.env.CDK_DEFAULT_ACCOUNT) {
  console.warn(
    `⚠️  Warning: AWS account not specified in cdk.json or CDK_DEFAULT_ACCOUNT. ` +
    `CDK will use the default account from AWS credentials.`
  );
}

// Environment for stacks
const env = {
  account: config.account || process.env.CDK_DEFAULT_ACCOUNT,
  region: config.region || process.env.CDK_DEFAULT_REGION || 'us-east-1',
};

console.log(`\n🚀 Deploying CO2 Anomaly Analysis System`);
console.log(`   Environment: ${config.environment}`);
console.log(`   Region: ${env.region}`);
console.log(`   Account: ${env.account || '(default)'}\n`);

// ========================================
// Layer 1: BaseStack - Foundation
// ========================================

const baseStack = new BaseStack(app, 'BaseStack', config, {
  env,
  description: 'Foundation layer: IAM roles, secrets, and configuration parameters',
  tags: {
    Layer: '1-Foundation',
  },
});

// ========================================
// Layer 2: NetworkStack - Network (Optional)
// ========================================

const networkStack = new NetworkStack(app, 'NetworkStack', config, {
  env,
  description: 'Network layer: VPC, security groups, and VPC endpoints (optional)',
  tags: {
    Layer: '2-Network',
  },
});

networkStack.addDependency(baseStack);

// ========================================
// Layer 3: StorageStack - Data
// ========================================

const storageStack = new StorageStack(app, 'StorageStack', config, {
  env,
  description: 'Data layer: DynamoDB cache table and S3 buckets',
  lambdaExecutionRole: baseStack.lambdaExecutionRole,
  tags: {
    Layer: '3-Data',
  },
});

storageStack.addDependency(baseStack);

// ========================================
// Layer 4: ComputeStack - Compute
// ========================================

const computeStack = new ComputeStack(app, 'ComputeStack', config, {
  env,
  description: 'Compute layer: Lambda function for reasoning API',
  lambdaExecutionRole: baseStack.lambdaExecutionRole,
  cacheTable: storageStack.cacheTable,
  geminiApiKeySecret: baseStack.geminiApiKeySecret,
  tags: {
    Layer: '4-Compute',
  },
});

computeStack.addDependency(baseStack);
computeStack.addDependency(storageStack);

// ========================================
// Layer 5: FrontendStack - Frontend
// ========================================

const frontendStack = new FrontendStack(app, 'FrontendStack', config, {
  env,
  description: 'Frontend layer: CloudFront distribution and static website',
  staticWebsiteBucket: storageStack.staticWebsiteBucket,
  geoJsonBucket: storageStack.geoJsonBucket,
  // apiGateway will be added when ApiStack is implemented
  tags: {
    Layer: '5-Frontend',
  },
});

frontendStack.addDependency(storageStack);

// ========================================
// Layer 6: MonitoringStack - Observability
// ========================================

const monitoringStack = new MonitoringStack(app, 'MonitoringStack', config, {
  env,
  description: 'Observability layer: CloudWatch dashboards, alarms, and SNS topics',
  reasoningFunction: computeStack.reasoningFunction,
  cacheTable: storageStack.cacheTable,
  // apiGateway will be added when ApiStack is implemented
  tags: {
    Layer: '6-Observability',
  },
});

monitoringStack.addDependency(computeStack);
monitoringStack.addDependency(storageStack);

// ========================================
// Synthesize CloudFormation Templates
// ========================================

app.synth();

console.log(`✅ CDK app synthesized successfully\n`);
console.log(`📋 Stacks to deploy:`);
console.log(`   1. BaseStack`);
console.log(`   2. NetworkStack`);
console.log(`   3. StorageStack`);
console.log(`   4. ComputeStack`);
console.log(`   5. FrontendStack`);
console.log(`   6. MonitoringStack\n`);
console.log(`💡 Deploy with: cdk deploy --all --context environment=${environmentName}\n`);
