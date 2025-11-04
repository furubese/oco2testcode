/**
 * FrontendStack - Frontend Layer
 *
 * This stack creates:
 * - CloudFront distribution for static website hosting
 * - S3 bucket policies for CloudFront access via OAI
 * - CORS configuration on S3 buckets
 * - Custom error pages (403, 404)
 * - HTTPS support with default CloudFront certificate
 * - Parameter Store exports for CloudFront URL
 *
 * Dependencies:
 * - StorageStack: staticWebsiteBucket, geoJsonBucket, originAccessIdentity
 */

import * as cdk from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import * as origins from 'aws-cdk-lib/aws-cloudfront-origins';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as s3deploy from 'aws-cdk-lib/aws-s3-deployment';
import { Construct } from 'constructs';
import { EnvironmentConfig, getResourceName, getResourceTags } from '../config/environment';
import * as path from 'path';
import { NagSuppressions } from 'cdk-nag';

export interface FrontendStackProps extends cdk.StackProps {
  staticWebsiteBucket: s3.IBucket;
  geoJsonBucket: s3.IBucket;
  originAccessIdentity: cloudfront.OriginAccessIdentity;
}

export class FrontendStack extends cdk.Stack {
  public readonly distribution: cloudfront.Distribution;
  public readonly cloudFrontUrl: string;

  constructor(scope: Construct, id: string, config: EnvironmentConfig, props: FrontendStackProps) {
    super(scope, id, props);

    // Apply resource tags
    const tags = getResourceTags(config);
    Object.entries(tags).forEach(([key, value]) => {
      cdk.Tags.of(this).add(key, value);
    });

    // ===========================
    // CORS Configuration for S3 Buckets
    // ===========================

    // Note: CORS must be configured on the underlying S3 bucket resources
    // Since we receive IBucket interfaces, we need to access the underlying CfnBucket
    // This is done by casting to s3.Bucket and using addCorsRule

    const staticBucket = props.staticWebsiteBucket as s3.Bucket;
    const geoJsonBucket = props.geoJsonBucket as s3.Bucket;

    // CORS for static website bucket
    staticBucket.addCorsRule({
      allowedOrigins: ['*'],
      allowedMethods: [s3.HttpMethods.GET, s3.HttpMethods.HEAD],
      allowedHeaders: ['*'],
      exposedHeaders: ['ETag'],
      maxAge: 3600,
    });

    // CORS for GeoJSON bucket
    geoJsonBucket.addCorsRule({
      allowedOrigins: ['*'],
      allowedMethods: [s3.HttpMethods.GET, s3.HttpMethods.HEAD],
      allowedHeaders: ['*'],
      exposedHeaders: ['ETag'],
      maxAge: 3600,
    });

    // ===========================
    // CloudFront Distribution
    // ===========================

    // Create CloudFront distribution with S3 origins
    this.distribution = new cloudfront.Distribution(this, 'Distribution', {
      comment: `${config.projectName} ${config.environment} - CO2 Analysis Frontend`,
      defaultRootObject: 'sample_calendar.html',

      // Default behavior - static website content
      defaultBehavior: {
        origin: new origins.S3Origin(staticBucket, {
          originAccessIdentity: props.originAccessIdentity,
        }),
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        allowedMethods: cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
        cachedMethods: cloudfront.CachedMethods.CACHE_GET_HEAD_OPTIONS,
        compress: true,
        cachePolicy: cloudfront.CachePolicy.CACHING_OPTIMIZED,
        originRequestPolicy: cloudfront.OriginRequestPolicy.CORS_S3_ORIGIN,
        responseHeadersPolicy: cloudfront.ResponseHeadersPolicy.CORS_ALLOW_ALL_ORIGINS,
      },

      // Additional behavior for GeoJSON data
      additionalBehaviors: {
        '/data/geojson/*': {
          origin: new origins.S3Origin(geoJsonBucket, {
            originAccessIdentity: props.originAccessIdentity,
          }),
          viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
          allowedMethods: cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
          cachedMethods: cloudfront.CachedMethods.CACHE_GET_HEAD_OPTIONS,
          compress: true,
          cachePolicy: cloudfront.CachePolicy.CACHING_OPTIMIZED,
          originRequestPolicy: cloudfront.OriginRequestPolicy.CORS_S3_ORIGIN,
          responseHeadersPolicy: cloudfront.ResponseHeadersPolicy.CORS_ALLOW_ALL_ORIGINS,
        },
      },

      // Custom error responses
      errorResponses: [
        {
          httpStatus: 403,
          responseHttpStatus: 404,
          responsePagePath: '/404.html',
          ttl: cdk.Duration.minutes(5),
        },
        {
          httpStatus: 404,
          responseHttpStatus: 404,
          responsePagePath: '/404.html',
          ttl: cdk.Duration.minutes(5),
        },
      ],

      // Price class - optimize for cost in dev, performance in prod
      priceClass: config.environment === 'prod'
        ? cloudfront.PriceClass.PRICE_CLASS_ALL
        : cloudfront.PriceClass.PRICE_CLASS_100,

      // Enable IPv6
      enableIpv6: true,

      // Enable logging in production
      enableLogging: config.environment !== 'dev',
      logBucket: config.environment !== 'dev' ? new s3.Bucket(this, 'CloudFrontLogsBucket', {
        bucketName: getResourceName(config, 'cloudfront-logs'),
        encryption: s3.BucketEncryption.S3_MANAGED,
        blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
        removalPolicy: cdk.RemovalPolicy.DESTROY,
        autoDeleteObjects: true,
        lifecycleRules: [
          {
            enabled: true,
            expiration: cdk.Duration.days(config.logRetentionDays),
          },
        ],
      }) : undefined,
      logFilePrefix: 'cloudfront/',
      logIncludesCookies: false,

      // Minimum TLS version
      minimumProtocolVersion: cloudfront.SecurityPolicyProtocol.TLS_V1_2_2021,

      // HTTP version
      httpVersion: cloudfront.HttpVersion.HTTP2_AND_3,
    });

    // Store CloudFront URL
    this.cloudFrontUrl = `https://${this.distribution.distributionDomainName}`;

    // ===========================
    // Deploy Static Website Files
    // ===========================

    // Deploy sample_calendar.html, config.js, and other static files
    new s3deploy.BucketDeployment(this, 'DeployWebsite', {
      sources: [
        s3deploy.Source.asset(path.join(__dirname, '../../'), {
          exclude: [
            '*',
            '!sample_calendar.html',
            '!config.js',
            '!404.html',
          ],
        }),
      ],
      destinationBucket: staticBucket,
      distribution: this.distribution,
      distributionPaths: ['/*'],
      prune: true,
      retainOnDelete: false,
    });

    // Create 404.html error page if it doesn't exist
    new s3deploy.BucketDeployment(this, 'Deploy404Page', {
      sources: [
        s3deploy.Source.data('404.html', `<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>404 - Page Not Found</title>
  <style>
    body {
      margin: 0;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100vh;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
    }
    .container {
      text-align: center;
      padding: 40px;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 20px;
      backdrop-filter: blur(10px);
      box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
    }
    h1 {
      font-size: 72px;
      margin: 0;
      font-weight: 700;
    }
    p {
      font-size: 24px;
      margin: 20px 0;
    }
    a {
      color: white;
      text-decoration: none;
      padding: 12px 30px;
      background: rgba(255, 255, 255, 0.2);
      border-radius: 25px;
      display: inline-block;
      margin-top: 20px;
      transition: background 0.3s;
    }
    a:hover {
      background: rgba(255, 255, 255, 0.3);
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>404</h1>
    <p>ページが見つかりません</p>
    <p>Page Not Found</p>
    <a href="/">ホームに戻る / Return to Home</a>
  </div>
</body>
</html>`),
      ],
      destinationBucket: staticBucket,
    });

    // ===========================
    // Parameter Store Exports
    // ===========================

    // CloudFront Distribution Domain Name
    new ssm.StringParameter(this, 'CloudFrontDomainName', {
      parameterName: `/${config.projectName}/${config.environment}/frontend/cloudfront/domain-name`,
      stringValue: this.distribution.distributionDomainName,
      description: 'CloudFront distribution domain name',
      tier: ssm.ParameterTier.STANDARD,
    });

    // CloudFront Distribution ID
    new ssm.StringParameter(this, 'CloudFrontDistributionIdParam', {
      parameterName: `/${config.projectName}/${config.environment}/frontend/cloudfront/distribution-id`,
      stringValue: this.distribution.distributionId,
      description: 'CloudFront distribution ID',
      tier: ssm.ParameterTier.STANDARD,
    });

    // CloudFront URL (HTTPS)
    new ssm.StringParameter(this, 'CloudFrontUrl', {
      parameterName: `/${config.projectName}/${config.environment}/frontend/cloudfront/url`,
      stringValue: this.cloudFrontUrl,
      description: 'CloudFront HTTPS URL for frontend',
      tier: ssm.ParameterTier.STANDARD,
    });

    // Static Website Bucket Name
    new ssm.StringParameter(this, 'StaticWebsiteBucketName', {
      parameterName: `/${config.projectName}/${config.environment}/frontend/s3/website-bucket-name`,
      stringValue: staticBucket.bucketName,
      description: 'S3 static website bucket name',
      tier: ssm.ParameterTier.STANDARD,
    });

    // GeoJSON Bucket Name
    new ssm.StringParameter(this, 'GeoJsonBucketName', {
      parameterName: `/${config.projectName}/${config.environment}/frontend/s3/geojson-bucket-name`,
      stringValue: geoJsonBucket.bucketName,
      description: 'S3 GeoJSON data bucket name',
      tier: ssm.ParameterTier.STANDARD,
    });

    // ===========================
    // CloudFormation Outputs
    // ===========================

    new cdk.CfnOutput(this, 'CloudFrontDistributionDomainName', {
      value: this.distribution.distributionDomainName,
      description: 'CloudFront distribution domain name',
      exportName: getResourceName(config, 'cloudfront-domain'),
    });

    new cdk.CfnOutput(this, 'CloudFrontDistributionId', {
      value: this.distribution.distributionId,
      description: 'CloudFront distribution ID for cache invalidation',
      exportName: getResourceName(config, 'cloudfront-id'),
    });

    new cdk.CfnOutput(this, 'WebsiteUrl', {
      value: this.cloudFrontUrl,
      description: 'HTTPS URL for the CO2 analysis frontend',
      exportName: getResourceName(config, 'website-url'),
    });

    new cdk.CfnOutput(this, 'StaticBucketName', {
      value: staticBucket.bucketName,
      description: 'S3 bucket name for static website files',
      exportName: getResourceName(config, 'static-bucket-name'),
    });

    new cdk.CfnOutput(this, 'GeoJsonBucketName', {
      value: geoJsonBucket.bucketName,
      description: 'S3 bucket name for GeoJSON data files',
      exportName: getResourceName(config, 'geojson-bucket-name'),
    });

    // ===========================
    // CDK Nag Suppressions
    // ===========================

    // Suppress CloudFront logging warning for dev environment
    if (config.environment === 'dev') {
      NagSuppressions.addResourceSuppressions(
        this.distribution,
        [
          {
            id: 'AwsSolutions-CFR1',
            reason: 'CloudFront access logging is disabled in development to reduce costs. Enabled in staging/production.',
          },
          {
            id: 'AwsSolutions-CFR2',
            reason: 'WAF is not required in development environment. Will be enabled in production for DDoS protection.',
          },
        ],
      );
    }

    // Suppress CloudFront default certificate warning (custom domain would require ACM certificate)
    NagSuppressions.addResourceSuppressions(
      this.distribution,
      [
        {
          id: 'AwsSolutions-CFR4',
          reason: 'Using default CloudFront certificate. For custom domain, ACM certificate would be configured separately.',
        },
      ],
    );

    // Suppress S3 bucket logging if not in production
    if (config.environment !== 'prod') {
      NagSuppressions.addResourceSuppressions(
        staticBucket,
        [
          {
            id: 'AwsSolutions-S1',
            reason: 'S3 server access logging disabled in non-production environments to reduce costs.',
          },
        ],
      );
      NagSuppressions.addResourceSuppressions(
        geoJsonBucket,
        [
          {
            id: 'AwsSolutions-S1',
            reason: 'S3 server access logging disabled in non-production environments to reduce costs.',
          },
        ],
      );
    }
  }
}
