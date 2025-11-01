import * as cdk from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import { Construct } from 'constructs';
import { EnvironmentConfig } from '../config/environment';

export interface FrontendStackProps extends cdk.StackProps {
  staticWebsiteBucket: s3.IBucket;
  geoJsonBucket: s3.IBucket;
  originAccessIdentity: cloudfront.IOriginAccessIdentity;
}

/**
 * FrontendStack - Frontend Layer (STUB)
 *
 * TODO: Implement full FrontendStack functionality
 * This is a stub implementation to allow MonitoringStack compilation
 */
export class FrontendStack extends cdk.Stack {
  constructor(scope: Construct, id: string, config: EnvironmentConfig, props: FrontendStackProps) {
    super(scope, id, props);

    // Stub implementation - to be replaced with actual implementation
  }
}
