/**
 * Frontend Configuration
 *
 * This file contains configuration values that are environment-specific.
 * It will be updated during deployment with actual values from AWS Parameter Store.
 */

const CONFIG = {
  // API Gateway URL - will be populated from Parameter Store during deployment
  // Format: https://{api-id}.execute-api.{region}.amazonaws.com/{stage}
  API_GATEWAY_URL: 'http://localhost:5000', // Default to local development

  // CloudFront URL - will be populated from CloudFormation during deployment
  // For local development, this will be empty and fall back to relative paths
  CLOUDFRONT_URL: '{{CLOUDFRONT_URL}}',

  // S3 GeoJSON Bucket URL - Use CloudFront URL for secure access to GeoJSON data
  // Direct S3 URL will not work due to BlockPublicAccess settings
  // For local development, this will be empty and fall back to relative paths
  GEOJSON_BASE_URL: '{{GEOJSON_BASE_URL}}',

  // Environment
  ENVIRONMENT: 'dev',

  // Cache settings
  CACHE_ENABLED: true,

  // API endpoints
  ENDPOINTS: {
    REASONING: '/reasoning', // API Gateway endpoint path
    GEOJSON: '/data/geojson', // CloudFront path for GeoJSON files
  }
};

// Make CONFIG available globally
window.APP_CONFIG = CONFIG;
