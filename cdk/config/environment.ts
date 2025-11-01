/**
 * Environment Configuration for CDK Stacks
 *
 * This file defines environment-specific configuration that can be used across all stacks.
 * Configuration is loaded from cdk.json's environmentConfig section.
 */

export interface EnvironmentConfig {
  account: string;
  region: string;
  environment: 'dev' | 'staging' | 'prod';
  projectName: string;
  appName: string;
  provisionedConcurrency: number;
  wafEnabled: boolean;
  enableXRay: boolean;
  logRetentionDays: number;
  alarmEmail: string;
  cacheTtlDays: number;
  apiThrottling: {
    rateLimit: number;
    burstLimit: number;
  };
}

/**
 * Get environment configuration from CDK context
 */
export function getEnvironmentConfig(context: any, env: string): EnvironmentConfig {
  const config = context.environmentConfig?.[env];

  if (!config) {
    throw new Error(
      `Environment configuration not found for: ${env}. ` +
      `Available environments: ${Object.keys(context.environmentConfig || {}).join(', ')}`
    );
  }

  // Validate required fields
  if (!config.region) {
    throw new Error(`Region is required in environment config for: ${env}`);
  }

  return config;
}

/**
 * Generate resource name with environment prefix
 */
export function getResourceName(config: EnvironmentConfig, resourceName: string): string {
  return `${config.projectName}-${config.environment}-${resourceName}`;
}

/**
 * Generate tags for AWS resources
 */
export function getResourceTags(config: EnvironmentConfig): Record<string, string> {
  return {
    Project: config.projectName,
    Environment: config.environment,
    Application: config.appName,
    ManagedBy: 'CDK',
    CreatedBy: 'AWS-CDK',
  };
}
