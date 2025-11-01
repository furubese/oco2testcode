/**
 * StorageStack - Data Layer (STUB)
 *
 * This is a stub implementation for dependency resolution.
 * Full implementation should be completed in a separate task.
 *
 * This stack should create:
 * - DynamoDB cache table
 * - S3 buckets for static website and GeoJSON data
 * - CloudFront Origin Access Identity
 */

import * as cdk from 'aws-cdk-lib';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import { Construct } from 'constructs';
import { EnvironmentConfig, getResourceName, getResourceTags } from '../config/environment';

export class StorageStack extends cdk.Stack {
  public readonly cacheTable: dynamodb.Table;
  public readonly staticWebsiteBucket: s3.Bucket;
  public readonly geoJsonBucket: s3.Bucket;
  public readonly originAccessIdentity: cloudfront.OriginAccessIdentity;

  constructor(scope: Construct, id: string, config: EnvironmentConfig, props?: cdk.StackProps) {
    super(scope, id, props);

    // Apply resource tags
    const tags = getResourceTags(config);
    Object.entries(tags).forEach(([key, value]) => {
      cdk.Tags.of(this).add(key, value);
    });

    // DynamoDB Cache Table
    this.cacheTable = new dynamodb.Table(this, 'CacheTable', {
      tableName: getResourceName(config, 'cache'),
      partitionKey: {
        name: 'cache_key',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
      pointInTimeRecovery: config.environment === 'prod',
      removalPolicy: config.environment === 'prod' ? cdk.RemovalPolicy.RETAIN : cdk.RemovalPolicy.DESTROY,
      timeToLiveAttribute: 'ttl',
    });

    // Add GSI for querying by cached_at
    this.cacheTable.addGlobalSecondaryIndex({
      indexName: 'cached_at-index',
      partitionKey: {
        name: 'cached_at',
        type: dynamodb.AttributeType.STRING,
      },
      projectionType: dynamodb.ProjectionType.ALL,
    });

    // Static Website Bucket (stub)
    this.staticWebsiteBucket = new s3.Bucket(this, 'StaticWebsiteBucket', {
      bucketName: getResourceName(config, 'static-website'),
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    // GeoJSON Data Bucket (stub)
    this.geoJsonBucket = new s3.Bucket(this, 'GeoJsonBucket', {
      bucketName: getResourceName(config, 'geojson-data'),
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    // CloudFront Origin Access Identity (stub)
    this.originAccessIdentity = new cloudfront.OriginAccessIdentity(this, 'OAI', {
      comment: `OAI for ${config.projectName} ${config.environment}`,
    });

    // Grant read access to OAI
    this.staticWebsiteBucket.grantRead(this.originAccessIdentity);
    this.geoJsonBucket.grantRead(this.originAccessIdentity);

    // Outputs
    new cdk.CfnOutput(this, 'CacheTableName', {
      value: this.cacheTable.tableName,
      description: 'DynamoDB cache table name',
      exportName: getResourceName(config, 'cache-table-name'),
    });
  }
}
