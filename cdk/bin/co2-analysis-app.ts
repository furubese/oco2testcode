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
import { AwsSolutionsChecks } from 'cdk-nag';

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

// Load environment configuration from cdk.json
const cdkJson = require('../cdk.json');
const config = getEnvironmentConfig(cdkJson, environmentName);

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

// CDK will automatically infer dependencies based on resource references
// networkStack.addDependency(baseStack);

// ========================================
// Layer 3: StorageStack - Data
// ========================================

const storageStack = new StorageStack(app, 'StorageStack', config, {
  env,
  description: 'Data layer: DynamoDB cache table and S3 buckets',
  tags: {
    Layer: '3-Data',
  },
});

// CDK will automatically infer dependencies based on resource references
// storageStack.addDependency(baseStack);

// ========================================
// Layer 4: ComputeStack - Compute
// ========================================

const computeStack = new ComputeStack(app, 'ComputeStack', {
  env,
  description: 'Compute layer: Lambda function for reasoning API',
  config: config,
  lambdaExecutionRole: baseStack.lambdaExecutionRole,
  cacheTable: storageStack.cacheTable,
  geminiApiKeySecret: baseStack.geminiApiKeySecret,
  tags: {
    Layer: '4-Compute',
  },
});

// CDK will automatically infer dependencies based on resource references
// computeStack.addDependency(baseStack);
// computeStack.addDependency(storageStack);

// ========================================
// Layer 5: FrontendStack - Frontend
// ========================================

const frontendStack = new FrontendStack(app, 'FrontendStack', {
  env,
  description: 'Frontend layer: CloudFront distribution and static website',
  config: config,
  staticWebsiteBucket: storageStack.staticWebsiteBucket,
  geoJsonBucket: storageStack.geoJsonBucket,
  originAccessIdentity: storageStack.originAccessIdentity,
  tags: {
    Layer: '5-Frontend',
  },
});

// CDK will automatically infer dependencies based on resource references
// frontendStack.addDependency(storageStack);

// ========================================
// Layer 6: MonitoringStack - Observability
// ========================================

const monitoringStack = new MonitoringStack(app, 'MonitoringStack', {
  env,
  description: 'Observability layer: CloudWatch dashboards, alarms, and SNS topics',
  config: config,
  lambdaFunction: computeStack.reasoningFunction,
  api: computeStack.api,
  cacheTable: storageStack.cacheTable,
  tags: {
    Layer: '6-Observability',
  },
});

// CDK will automatically infer dependencies based on resource references
// monitoringStack.addDependency(computeStack);
// monitoringStack.addDependency(storageStack);

// ========================================
// CDK Nag - Security and Best Practices Validation
// ========================================

// Apply AWS Solutions security checks to all stacks
cdk.Aspects.of(app).add(new AwsSolutionsChecks({ verbose: true }));

console.log(`🔒 CDK Nag enabled: AwsSolutionsChecks will validate security best practices\n`);

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
