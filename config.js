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

  // CloudFront URL - will be populated from Parameter Store during deployment
  CLOUDFRONT_URL: 'https://d2t60ct01pkwhj.cloudfront.net',

  // S3 GeoJSON Bucket URL - Use CloudFront URL for secure access to GeoJSON data
  // Direct S3 URL will not work due to BlockPublicAccess settings
  GEOJSON_BASE_URL: 'https://d2t60ct01pkwhj.cloudfront.net/data/geojson',

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
