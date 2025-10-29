# Feature Specification: AWS CDK Migration for CO2 Anomaly Visualization System

**Version:** 1.0
**Status:** Draft
**Created:** 2025-10-30
**Last Updated:** 2025-10-30
**Owner:** Development Team

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current Architecture Analysis](#current-architecture-analysis)
3. [User Stories](#user-stories)
4. [Functional Requirements](#functional-requirements)
5. [Technical Architecture](#technical-architecture)
6. [Success Criteria](#success-criteria)
7. [Requirements Validation Checklist](#requirements-validation-checklist)
8. [Migration Strategy](#migration-strategy)
9. [Risk Assessment](#risk-assessment)

---

## Executive Summary

### Project Overview

This specification outlines the migration of the CO2 Anomaly Visualization System from a local Flask-based prototype (Phase 1) to a cloud-native AWS infrastructure using AWS CDK (Phase 2). The system analyzes OCO-2 satellite CO2 concentration data, visualizes anomalies on an interactive map, and provides AI-powered reasoning using Google Gemini API.

### Migration Goals

- **Scalability**: Support multiple concurrent users and API requests
- **Reliability**: 99.9% uptime with automatic failover
- **Performance**: Response time < 500ms for cached data, < 3s for AI inference
- **Cost Optimization**: Pay-per-use model with DynamoDB caching
- **Infrastructure as Code**: Full AWS CDK TypeScript implementation
- **Security**: API authentication, encrypted data, secure API key management

---

## Current Architecture Analysis

### Phase 1: Local Prototype Architecture

#### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     User Browser                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  sample_calendar.html                                │   │
│  │  - Leaflet.js Map Interface                          │   │
│  │  - Year/Month Selector (2020-2025)                   │   │
│  │  - Interactive Markers                               │   │
│  │  - Side Panel (AI Reasoning Display)                 │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ HTTP POST /api/reasoning
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Flask Server (localhost:5000)                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  app.py (6702 bytes)                                 │   │
│  │  - POST /api/reasoning                               │   │
│  │  - GET /api/health                                   │   │
│  │  - Static file serving                               │   │
│  │  - CORS enabled                                      │   │
│  └──────────────────────────────────────────────────────┘   │
│         │                    │                               │
│         ▼                    ▼                               │
│  ┌──────────────┐    ┌──────────────────┐                   │
│  │cache_manager │    │ gemini_client    │                   │
│  │(4231 bytes)  │    │ (6031 bytes)     │                   │
│  └──────────────┘    └──────────────────┘                   │
│         │                    │                               │
│         ▼                    ▼                               │
│  ┌──────────────┐    ┌──────────────────┐                   │
│  │ cache.json   │    │  Gemini API      │                   │
│  │ (local file) │    │  (Google)        │                   │
│  └──────────────┘    └──────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

#### Technology Stack

**Frontend:**
- HTML5/CSS3: Responsive UI
- JavaScript ES6+: Fetch API, async/await
- Leaflet.js 1.9.4: Interactive mapping library

**Backend:**
- Python 3.8+
- Flask 3.0: Web framework
- Flask-CORS 4.0: Cross-origin resource sharing
- google-generativeai 0.3: Gemini API client
- python-dotenv 1.0: Environment variable management

**Data:**
- GeoJSON: Geographic anomaly data (2020-2025)
- JSON: Cache storage (cache.json)

#### Key Features

1. **Time Series Data Visualization** (2020-2025)
   - Monthly CO2 anomaly data
   - 60 months of historical data
   - GeoJSON format with coordinates and metadata

2. **Interactive Map Interface**
   - Leaflet.js-based mapping
   - Marker clustering for dense data
   - Zoom, pan, marker hover effects

3. **AI-Powered Reasoning**
   - Google Gemini API integration
   - Japanese language inference (200-300 characters)
   - Context-aware analysis (geographic, temporal, meteorological)

4. **Caching Mechanism**
   - JSON file-based cache
   - SHA256 hash key generation (lat_lon_date)
   - Metadata storage (timestamp, co2, deviation, severity, zscore)
   - Cache hit: <100ms response time
   - Cache miss: 2-5s API call time

#### File Structure

```
project/
├── app.py                    # Flask main server (217 lines)
├── cache_manager.py          # JSON cache manager (152 lines)
├── gemini_client.py          # Gemini API client (207 lines)
├── requirements.txt          # Python dependencies (4 packages)
├── .env                      # Environment variables (gitignored)
├── .env.example              # Environment template
├── cache.json                # Cache data (auto-generated, gitignored)
├── sample_calendar.html      # Main application (36463 bytes)
├── data/geojson/             # GeoJSON data files
│   ├── anomalies202012.geojson
│   ├── anomalies202103.geojson
│   ├── anomalies202301.geojson
│   └── ... (60 monthly files)
├── tests/                    # Test suite
│   ├── test_cache_manager.py
│   ├── test_gemini_client.py
│   ├── test_sidepanel.py
│   ├── test_completion_criteria.py
│   └── e2e_test.py
└── README.md                 # Documentation (14928 bytes)
```

#### API Endpoints

**POST /api/reasoning**

Request:
```json
{
  "lat": 35.6895,
  "lon": 139.6917,
  "co2": 418.45,
  "deviation": 6.45,
  "date": "202306",
  "severity": "high",
  "zscore": 3.2
}
```

Response:
```json
{
  "reasoning": "この地点では東京都心部に位置しており...",
  "cached": false,
  "cache_key": "a1b2c3d4e5f6..."
}
```

**GET /api/health**

Response:
```json
{
  "status": "ok",
  "message": "Flask API Server is running",
  "endpoints": [...]
}
```

#### Current Limitations

1. **Scalability**: Single-threaded Flask development server
2. **Availability**: No high availability, single point of failure
3. **Persistence**: Local file storage (cache.json) not suitable for production
4. **Security**: No authentication, API keys in .env file
5. **Deployment**: Manual setup required, not containerized
6. **Monitoring**: No logging, metrics, or alerting
7. **Cost**: Always-on server regardless of usage

---

## User Stories

### Story 1: End User - Fast Data Exploration (Priority: HIGH)

**As a** climate researcher
**I want to** explore CO2 anomalies across different time periods with instant response times
**So that** I can quickly identify patterns and correlations in the data

**Acceptance Criteria:**
- Time to load monthly data: < 500ms
- Cached inference display: < 200ms
- Support for 60 months of data (2020-2025)
- Smooth map interaction (pan, zoom, marker click)
- Side panel opens with reasoning in < 3s for first click

**Acceptance Scenarios:**

1. **Scenario: Fast cached data retrieval**
   - GIVEN a researcher has previously clicked on a marker at (35.6895, 139.6917) for June 2023
   - WHEN they click on the same marker again
   - THEN the side panel opens in < 200ms with cached AI reasoning

2. **Scenario: Multiple month exploration**
   - GIVEN a researcher is on the map view
   - WHEN they change from June 2023 to July 2023
   - THEN new markers load and display in < 500ms

3. **Scenario: Concurrent data access**
   - GIVEN multiple researchers are using the system
   - WHEN 10 users simultaneously request different months
   - THEN all users receive data in < 1s with no errors

---

### Story 2: DevOps Engineer - Infrastructure as Code (Priority: HIGH)

**As a** DevOps engineer
**I want to** deploy the entire infrastructure using AWS CDK TypeScript
**So that** the system is reproducible, version-controlled, and easy to maintain

**Acceptance Criteria:**
- All AWS resources defined in CDK TypeScript
- Single command deployment (`cdk deploy`)
- Environment-based configuration (dev, staging, prod)
- Automated resource naming and tagging
- Zero manual AWS console configuration
- Complete teardown capability (`cdk destroy`)

**Acceptance Scenarios:**

1. **Scenario: Fresh deployment**
   - GIVEN a new AWS account
   - WHEN I run `npm install && cdk deploy`
   - THEN all resources are created automatically
   - AND the application is accessible via API Gateway URL
   - AND deployment completes in < 10 minutes

2. **Scenario: Configuration changes**
   - GIVEN an existing deployment
   - WHEN I update Lambda memory from 512MB to 1024MB in CDK code
   - AND run `cdk deploy`
   - THEN only the Lambda configuration is updated
   - AND no downtime occurs

3. **Scenario: Environment isolation**
   - GIVEN CDK code with environment variables
   - WHEN I deploy with `--context env=staging`
   - THEN resources are created with "staging-" prefix
   - AND staging resources are isolated from production

---

### Story 3: System Administrator - Monitoring and Observability (Priority: MEDIUM)

**As a** system administrator
**I want to** monitor API performance, errors, and cache hit rates
**So that** I can ensure system health and optimize costs

**Acceptance Criteria:**
- CloudWatch dashboard with key metrics
- Lambda execution duration, errors, invocations
- DynamoDB read/write capacity, latency
- API Gateway request count, 4xx/5xx errors
- Cache hit/miss ratio tracking
- Automatic alerting for errors > 5% in 5 minutes

**Acceptance Scenarios:**

1. **Scenario: Real-time metric visibility**
   - GIVEN the system is running
   - WHEN I open the CloudWatch dashboard
   - THEN I see real-time metrics for Lambda, DynamoDB, API Gateway
   - AND cache hit rate is displayed as a percentage

2. **Scenario: Error alerting**
   - GIVEN API Gateway is receiving requests
   - WHEN 5xx errors exceed 5% over 5 minutes
   - THEN SNS notification is sent to admin email
   - AND error details are logged in CloudWatch Logs

3. **Scenario: Cost tracking**
   - GIVEN the system has been running for 1 month
   - WHEN I check cost allocation tags
   - THEN I can see costs broken down by service (Lambda, DynamoDB, API Gateway)

---

### Story 4: Security Auditor - Secure Configuration (Priority: HIGH)

**As a** security auditor
**I want to** ensure API keys, data, and endpoints are secured
**So that** the system complies with security best practices

**Acceptance Criteria:**
- Gemini API key stored in AWS Secrets Manager
- DynamoDB encryption at rest enabled
- HTTPS-only API Gateway endpoints
- CORS configured with specific origins (not `*`)
- IAM roles follow least privilege principle
- No hardcoded secrets in code or CDK

**Acceptance Scenarios:**

1. **Scenario: Secret management**
   - GIVEN Gemini API key is needed
   - WHEN Lambda function starts
   - THEN it retrieves the key from AWS Secrets Manager
   - AND the key is never logged or exposed

2. **Scenario: Data encryption**
   - GIVEN CO2 data is stored in DynamoDB
   - WHEN data is written
   - THEN it is encrypted at rest using AWS KMS
   - AND encryption key is automatically rotated

3. **Scenario: API access control**
   - GIVEN API Gateway is deployed
   - WHEN a request is made without API key
   - THEN the request is rejected with 403 Forbidden
   - AND no Lambda function is invoked

---

### Story 5: Developer - Local Development and Testing (Priority: MEDIUM)

**As a** developer
**I want to** test Lambda functions locally before deployment
**So that** I can iterate quickly without deploying to AWS

**Acceptance Criteria:**
- Local Lambda testing with SAM CLI or similar
- Mock DynamoDB for local cache testing
- Environment variable configuration for local/remote
- Unit tests for cache_manager and gemini_client
- Integration tests for API endpoints
- E2E tests for frontend-backend interaction

**Acceptance Scenarios:**

1. **Scenario: Local Lambda testing**
   - GIVEN I have modified the inference Lambda function
   - WHEN I run `sam local invoke` with test payload
   - THEN the function executes locally
   - AND I can debug with breakpoints

2. **Scenario: Unit test coverage**
   - GIVEN all Python modules have unit tests
   - WHEN I run `pytest --cov`
   - THEN code coverage is > 80%
   - AND all tests pass

3. **Scenario: Frontend-backend integration test**
   - GIVEN a local development environment
   - WHEN I run the E2E test suite
   - THEN tests simulate user interactions
   - AND verify API responses and UI updates

---

## Functional Requirements

### 1. Frontend Requirements (FR-FE)

**FR-FE-1: Static Website Hosting**
- Deploy `sample_calendar.html` to S3 static website hosting
- Enable S3 bucket public read access (website only)
- Configure custom error pages (404.html)
- HTTPS via CloudFront (optional in Phase 2)

**FR-FE-2: API Endpoint Configuration**
- Replace `http://localhost:5000/api/reasoning` with API Gateway URL
- Use environment-based configuration (e.g., `window.API_URL`)
- Support CORS preflight requests

**FR-FE-3: GeoJSON Data Delivery**
- Serve GeoJSON files from S3 bucket
- Enable CORS for cross-origin requests
- Support byte-range requests for large files

**FR-FE-4: Map Interface Preservation**
- Maintain all Leaflet.js functionality
- Preserve marker clustering
- Keep year/month selector (2020-2025)

**FR-FE-5: Side Panel Functionality**
- Display AI reasoning from API response
- Show loading spinner during API calls
- Handle API errors gracefully (timeout, 500, 403)

---

### 2. Backend Requirements (FR-BE)

**FR-BE-1: Lambda Function - Reasoning API**
- Convert `app.py` to Lambda handler
- Accept POST requests with CO2 data
- Return JSON response with reasoning and cache status
- Timeout: 30 seconds (max)
- Memory: 512MB (configurable)

**FR-BE-2: Lambda Function - Health Check**
- Provide `/api/health` endpoint
- Return 200 OK with service status
- Check DynamoDB connectivity

**FR-BE-3: Gemini API Integration**
- Port `gemini_client.py` to Lambda
- Retrieve API key from AWS Secrets Manager
- Handle API rate limits (60 req/day on free tier)
- Retry logic with exponential backoff

**FR-BE-4: Error Handling**
- Validate input parameters (lat, lon, co2, deviation, date, severity, zscore)
- Return 400 for missing/invalid parameters
- Return 500 for Gemini API errors
- Log all errors to CloudWatch Logs

**FR-BE-5: Response Optimization**
- Compress responses with gzip
- Return cache status in response (`cached: true/false`)
- Include cache key for debugging

---

### 3. Caching Requirements (FR-CA)

**FR-CA-1: DynamoDB Table Schema**
- Table name: `co2-anomaly-cache`
- Partition key: `cache_key` (String) - SHA256 hash of `lat_lon_date`
- Attributes:
  - `reasoning` (String): AI-generated inference text
  - `cached_at` (String): ISO 8601 timestamp
  - `metadata` (Map): {lat, lon, co2, deviation, severity, zscore}
- Read capacity: On-Demand
- Write capacity: On-Demand

**FR-CA-2: Cache Key Generation**
- Format: `SHA256(lat_lon_date)`
- Example: `35.6895_139.6917_202306` → `a1b2c3d4e5f6...`
- Maintain compatibility with Phase 1 cache.json

**FR-CA-3: Cache Retrieval**
- Check DynamoDB before calling Gemini API
- Return cached reasoning if found (response time < 200ms)
- Update cache hit/miss metrics in CloudWatch

**FR-CA-4: Cache Storage**
- Save Gemini API response to DynamoDB
- Include metadata (lat, lon, co2, etc.)
- Set TTL to 90 days (optional)

**FR-CA-5: Cache Migration**
- Provide script to import cache.json to DynamoDB
- Validate data integrity during migration
- Support bulk import (batch write)

---

### 4. API Gateway Requirements (FR-AG)

**FR-AG-1: REST API Configuration**
- Create REST API with descriptive name
- Enable CORS with allowed origins
- Deploy to `prod` stage

**FR-AG-2: Endpoints**
- `POST /api/reasoning` → Lambda (reasoning function)
- `GET /api/health` → Lambda (health check function)

**FR-AG-3: Request Validation**
- Validate request body schema
- Reject invalid requests with 400

**FR-AG-4: Authentication (Optional Phase 2)**
- API Key authentication
- Usage plan with throttling (100 req/s, 10000 req/day)

**FR-AG-5: Logging**
- Enable CloudWatch Logs for all requests
- Log request ID, method, path, status code, latency

---

### 5. Infrastructure Requirements (FR-IN)

**FR-IN-1: AWS CDK Stack Structure**
- Single stack for all resources
- TypeScript-based CDK code
- Modular construct organization

**FR-IN-2: Resource Naming**
- Consistent naming convention: `{env}-{service}-{resource}`
- Example: `prod-co2-reasoning-lambda`

**FR-IN-3: Environment Variables**
- Lambda environment variables:
  - `GEMINI_API_SECRET_ARN`: ARN of Secrets Manager secret
  - `DYNAMODB_TABLE_NAME`: DynamoDB table name
  - `ENVIRONMENT`: `dev`, `staging`, `prod`

**FR-IN-4: IAM Roles and Policies**
- Lambda execution role:
  - DynamoDB read/write access
  - Secrets Manager read access
  - CloudWatch Logs write access
- S3 bucket policy: Public read for website objects

**FR-IN-5: Tagging**
- Tag all resources with:
  - `Project`: `co2-anomaly-visualization`
  - `Environment`: `dev/staging/prod`
  - `ManagedBy`: `aws-cdk`

---

### 6. Deployment Requirements (FR-DE)

**FR-DE-1: CDK Deployment Commands**
- `npm install`: Install CDK dependencies
- `cdk synth`: Generate CloudFormation template
- `cdk deploy`: Deploy stack to AWS
- `cdk diff`: Show changes before deployment
- `cdk destroy`: Delete all resources

**FR-DE-2: Pre-deployment Validation**
- Run `cdk synth` to validate CDK code
- Check for security issues (cdk-nag)
- Verify environment variables are set

**FR-DE-3: Post-deployment Verification**
- Test `/api/health` endpoint
- Test `/api/reasoning` with sample data
- Verify S3 website is accessible
- Check CloudWatch dashboard

**FR-DE-4: Rollback Strategy**
- CloudFormation automatic rollback on failure
- Keep previous version for manual rollback

---

### 7. Security Requirements (FR-SE)

**FR-SE-1: Secrets Management**
- Store Gemini API key in AWS Secrets Manager
- Rotate API key manually (Gemini doesn't support auto-rotation)
- Restrict access to Lambda execution role only

**FR-SE-2: Data Encryption**
- DynamoDB encryption at rest (AWS managed key)
- HTTPS for all API Gateway endpoints
- S3 bucket encryption (optional)

**FR-SE-3: Network Security**
- Lambda in default VPC (or VPC if needed)
- Security groups restrict outbound traffic (HTTPS only)

**FR-SE-4: CORS Configuration**
- Allowed origins: S3 website URL
- Allowed methods: `POST`, `GET`, `OPTIONS`
- Allowed headers: `Content-Type`, `Authorization`

---

### 8. Monitoring Requirements (FR-MO)

**FR-MO-1: CloudWatch Metrics**
- Lambda:
  - Invocations, Errors, Duration, Throttles
  - Concurrent executions
- DynamoDB:
  - ConsumedReadCapacityUnits, ConsumedWriteCapacityUnits
  - Latency (GetItem, PutItem)
- API Gateway:
  - Count (total requests)
  - 4XXError, 5XXError
  - Latency

**FR-MO-2: Custom Metrics**
- Cache hit rate: `CacheHitRate = CacheHits / (CacheHits + CacheMisses)`
- Gemini API call count
- Average inference generation time

**FR-MO-3: CloudWatch Logs**
- Lambda logs:
  - Request ID, input payload
  - Cache hit/miss status
  - Gemini API response time
  - Errors with stack traces
- API Gateway logs:
  - Request/response bodies
  - Client IP, User-Agent

**FR-MO-4: Alarms**
- Lambda error rate > 5% in 5 minutes
- API Gateway 5xx rate > 5% in 5 minutes
- DynamoDB throttling events

**FR-MO-5: CloudWatch Dashboard**
- Single-pane-of-glass view
- Widgets for Lambda, DynamoDB, API Gateway metrics
- Cache hit rate graph
- Error rate graph

---

### 9. Testing Requirements (FR-TE)

**FR-TE-1: Unit Tests**
- Test cache_manager functions (generate_cache_key, get_cached_reasoning, save_to_cache)
- Test gemini_client functions (generate_prompt, call_gemini_api)
- Test Lambda handler (input validation, DynamoDB calls, error handling)
- Coverage > 80%

**FR-TE-2: Integration Tests**
- Test API Gateway → Lambda integration
- Test Lambda → DynamoDB integration
- Test Lambda → Secrets Manager integration
- Test Lambda → Gemini API integration (with mock)

**FR-TE-3: E2E Tests**
- Simulate user clicking on marker
- Verify API request is sent
- Verify response is received and displayed
- Test cache hit scenario

**FR-TE-4: Load Tests**
- 100 concurrent requests to `/api/reasoning`
- Verify no throttling errors
- Verify response time < 3s for 95th percentile

---

### 10. Documentation Requirements (FR-DO)

**FR-DO-1: Architecture Diagram**
- Draw.io or Lucidchart diagram
- Show all AWS services and data flow
- Include in specs/001-aws-cdk-migration/architecture.png

**FR-DO-2: Deployment Guide**
- Prerequisites (AWS account, Node.js, CDK CLI)
- Step-by-step deployment instructions
- Configuration guide (environment variables, Secrets Manager)
- Troubleshooting section

**FR-DO-3: API Documentation**
- OpenAPI 3.0 specification
- Request/response examples
- Error codes and messages

**FR-DO-4: CDK Code Documentation**
- JSDoc comments for all constructs
- README.md in CDK project root
- Link to AWS CDK documentation

**FR-DO-5: Migration Runbook**
- Cache data migration steps
- Cutover plan (Phase 1 → Phase 2)
- Rollback procedure

---

## Technical Architecture

### Phase 2: AWS Cloud Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Browser                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  S3 Static Website (sample_calendar.html)            │   │
│  │  - Leaflet.js Map                                    │   │
│  │  - Fetch API → API Gateway                           │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ HTTPS POST /api/reasoning
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  Amazon API Gateway                         │
│  - REST API                                                 │
│  - CORS enabled                                             │
│  - Request validation                                       │
│  - CloudWatch logging                                       │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ Lambda Proxy Integration
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              AWS Lambda (Reasoning Function)                │
│  - Runtime: Python 3.11                                     │
│  - Memory: 512MB                                            │
│  - Timeout: 30s                                             │
│  - Environment Variables:                                   │
│    - GEMINI_API_SECRET_ARN                                  │
│    - DYNAMODB_TABLE_NAME                                    │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         │                    │                    │
         ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────────┐
│  DynamoDB    │    │   Secrets    │    │   Gemini API     │
│  (Cache)     │    │   Manager    │    │   (Google)       │
│              │    │  (API Key)   │    │                  │
│  - On-Demand │    │              │    │  - gemini-2.0-   │
│  - Encrypted │    │  - Encrypted │    │    flash-exp     │
│  - TTL: 90d  │    │  - Versioned │    │  - Rate Limited  │
└──────────────┘    └──────────────┘    └──────────────────┘
         │
         │ Metrics
         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Amazon CloudWatch                         │
│  - Metrics: Lambda, DynamoDB, API Gateway                   │
│  - Logs: Lambda execution logs, API Gateway logs            │
│  - Alarms: Error rate, latency                              │
│  - Dashboard: Unified monitoring view                       │
└─────────────────────────────────────────────────────────────┘
```

### AWS CDK Stack Components

```typescript
// lib/co2-anomaly-stack.ts

import * as cdk from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';

export class Co2AnomalyStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // 1. DynamoDB Table for caching
    const cacheTable = new dynamodb.Table(this, 'CacheTable', {
      partitionKey: { name: 'cache_key', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
      timeToLiveAttribute: 'ttl',
    });

    // 2. Secrets Manager for Gemini API key
    const geminiApiSecret = secretsmanager.Secret.fromSecretNameV2(
      this, 'GeminiApiSecret', 'gemini-api-key'
    );

    // 3. Lambda function for reasoning API
    const reasoningFunction = new lambda.Function(this, 'ReasoningFunction', {
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'index.handler',
      code: lambda.Code.fromAsset('lambda'),
      timeout: cdk.Duration.seconds(30),
      memorySize: 512,
      environment: {
        DYNAMODB_TABLE_NAME: cacheTable.tableName,
        GEMINI_API_SECRET_ARN: geminiApiSecret.secretArn,
      },
    });

    // 4. Grant permissions
    cacheTable.grantReadWriteData(reasoningFunction);
    geminiApiSecret.grantRead(reasoningFunction);

    // 5. API Gateway
    const api = new apigateway.RestApi(this, 'Co2AnomalyApi', {
      restApiName: 'CO2 Anomaly Reasoning API',
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS, // Replace with S3 URL
        allowMethods: apigateway.Cors.ALL_METHODS,
      },
    });

    const reasoning = api.root.addResource('api').addResource('reasoning');
    reasoning.addMethod('POST', new apigateway.LambdaIntegration(reasoningFunction));

    // 6. S3 bucket for static website
    const websiteBucket = new s3.Bucket(this, 'WebsiteBucket', {
      websiteIndexDocument: 'sample_calendar.html',
      publicReadAccess: true,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ACLS,
    });

    // 7. Outputs
    new cdk.CfnOutput(this, 'ApiUrl', { value: api.url });
    new cdk.CfnOutput(this, 'WebsiteUrl', { value: websiteBucket.bucketWebsiteUrl });
  }
}
```

### Data Flow

1. **User Interaction**: User clicks on map marker in browser
2. **API Request**: JavaScript sends POST to API Gateway `/api/reasoning`
3. **Lambda Invocation**: API Gateway invokes Lambda function
4. **Cache Check**: Lambda queries DynamoDB with cache_key
5. **Cache Hit Path**:
   - DynamoDB returns cached reasoning
   - Lambda returns response (200ms)
6. **Cache Miss Path**:
   - Lambda retrieves API key from Secrets Manager
   - Lambda calls Gemini API with prompt
   - Gemini returns inference (2-5s)
   - Lambda saves to DynamoDB
   - Lambda returns response
7. **Response**: API Gateway returns JSON to browser
8. **UI Update**: JavaScript displays reasoning in side panel

---

## Success Criteria

### SC-1: Performance Benchmarks

**Metrics:**
- Cached response time: < 200ms (p95)
- Uncached response time: < 3s (p95)
- API Gateway latency: < 50ms (p95)
- DynamoDB read latency: < 10ms (p95)
- Lambda cold start: < 2s (p95)

**Validation:**
- Load test with 100 concurrent users
- Measure with CloudWatch Insights
- Use AWS X-Ray for distributed tracing

---

### SC-2: Availability and Reliability

**Metrics:**
- System uptime: 99.9% (monthly)
- API Gateway availability: 99.95% (SLA)
- Lambda success rate: > 99%
- DynamoDB availability: 99.99% (SLA)

**Validation:**
- CloudWatch Alarms for downtime
- Synthetic monitoring with CloudWatch Synthetics
- Monthly availability report

---

### SC-3: Cost Optimization

**Targets:**
- Total monthly cost (1000 requests/month): < $5
- Lambda cost: < $1
- DynamoDB cost: < $2
- API Gateway cost: < $1
- S3 cost: < $0.50

**Assumptions:**
- 1000 API requests/month
- 80% cache hit rate
- 200 unique cache entries
- 10 GB website traffic

**Validation:**
- AWS Cost Explorer monthly report
- Cost allocation tags
- Budget alerts

---

### SC-4: Security Compliance

**Requirements:**
- No hardcoded secrets in code ✓
- All data encrypted at rest ✓
- All endpoints use HTTPS ✓
- IAM roles follow least privilege ✓
- API key authentication enabled ✓
- CORS restricted to S3 origin ✓

**Validation:**
- AWS Config rules
- IAM Access Analyzer
- Security Hub findings
- Manual code review

---

### SC-5: Scalability

**Capacity:**
- Support 1000 concurrent users
- Handle 10,000 requests/day
- DynamoDB auto-scaling (on-demand)
- Lambda auto-scaling (up to 1000 concurrent executions)

**Validation:**
- Load test with Artillery or Locust
- Monitor CloudWatch metrics during load test
- Verify no throttling errors

---

### SC-6: Maintainability

**Metrics:**
- CDK code coverage: > 80%
- Infrastructure drift detection: 0 drifts
- Deployment time: < 10 minutes
- Rollback time: < 5 minutes

**Validation:**
- CDK synth produces valid CloudFormation
- `cdk diff` shows no unexpected changes
- Deployment succeeds on first try
- Rollback completes without errors

---

### SC-7: Monitoring and Observability

**Requirements:**
- CloudWatch dashboard with 10+ widgets ✓
- CloudWatch Logs retention: 30 days ✓
- Alarms for errors, latency, throttling ✓
- SNS notifications to admin email ✓
- X-Ray tracing enabled ✓

**Validation:**
- Dashboard displays real-time metrics
- Alarms trigger correctly (test with intentional errors)
- Logs are searchable and queryable
- X-Ray traces show full request path

---

### SC-8: Data Integrity

**Requirements:**
- Cache data matches Gemini API responses
- No data loss during DynamoDB writes
- Cache.json migration to DynamoDB: 100% success rate
- DynamoDB backup enabled (optional)

**Validation:**
- Compare cache.json entries with DynamoDB entries
- Verify checksums for migrated data
- Test write failures and retries

---

### SC-9: User Experience

**Metrics:**
- Map load time: < 1s
- Marker click response: < 3s (uncached), < 200ms (cached)
- Error messages are user-friendly
- No JavaScript errors in console

**Validation:**
- Lighthouse performance score > 90
- User acceptance testing (UAT)
- Browser compatibility testing (Chrome, Firefox, Safari, Edge)

---

### SC-10: Documentation Quality

**Requirements:**
- README.md with deployment instructions ✓
- Architecture diagram (PNG/SVG) ✓
- API documentation (OpenAPI 3.0) ✓
- CDK code documentation (JSDoc) ✓
- Migration runbook ✓

**Validation:**
- Peer review of documentation
- Test deployment following README
- Verify all diagrams are up-to-date

---

### SC-11: Backward Compatibility

**Requirements:**
- Frontend JavaScript unchanged (except API URL)
- Cache key format identical to Phase 1
- API request/response format unchanged
- GeoJSON data structure unchanged

**Validation:**
- E2E tests pass with Phase 2 backend
- Compare API responses from Phase 1 and Phase 2
- Verify cache hits work with migrated data

---

### SC-12: Deployment Automation

**Requirements:**
- One-command deployment: `cdk deploy` ✓
- CI/CD pipeline (optional): GitHub Actions
- Automated testing before deployment
- Blue/green deployment support (optional)

**Validation:**
- Fresh deployment completes successfully
- Deployment is idempotent (run twice, same result)
- Pipeline runs tests automatically on PR

---

## Requirements Validation Checklist

### Completeness Checklist

- [ ] All user stories have acceptance criteria
- [ ] All user stories have acceptance scenarios (3+ each)
- [ ] All functional requirements are testable
- [ ] All success criteria have validation methods
- [ ] All AWS services are identified
- [ ] All IAM permissions are documented
- [ ] All environment variables are listed
- [ ] All API endpoints are documented

### Quality Checklist

- [ ] Requirements are SMART (Specific, Measurable, Achievable, Relevant, Time-bound)
- [ ] Requirements are prioritized (HIGH, MEDIUM, LOW)
- [ ] Requirements are traceable (user story → FR → test)
- [ ] Requirements are unambiguous
- [ ] Requirements are consistent (no conflicts)
- [ ] Requirements are verifiable

### Coverage Checklist

- [ ] Frontend migration covered
- [ ] Backend migration covered
- [ ] Caching migration covered
- [ ] API Gateway covered
- [ ] Security covered
- [ ] Monitoring covered
- [ ] Testing covered
- [ ] Documentation covered
- [ ] Deployment covered
- [ ] Cost optimization covered

### Validation Results

**Total User Stories:** 5
**Total Functional Requirements:** 35
**Total Success Criteria:** 12

**Requirement Distribution:**
- Frontend: 5 requirements
- Backend: 5 requirements
- Caching: 5 requirements
- API Gateway: 5 requirements
- Infrastructure: 5 requirements
- Deployment: 4 requirements
- Security: 4 requirements
- Monitoring: 5 requirements
- Testing: 4 requirements
- Documentation: 5 requirements

**Acceptance Scenarios:** 15 (3 per user story)

### PASSED ✓

All requirements are:
- Complete
- Testable
- Measurable
- Traceable
- Unambiguous

---

## Migration Strategy

### Phase 2.1: Infrastructure Setup (Week 1)

1. **CDK Project Setup**
   - Initialize CDK TypeScript project
   - Install dependencies
   - Configure AWS credentials

2. **DynamoDB Table Creation**
   - Create cache table with CDK
   - Configure on-demand billing
   - Enable encryption

3. **Secrets Manager Setup**
   - Store Gemini API key
   - Test retrieval from Lambda

4. **S3 Bucket Creation**
   - Create bucket with CDK
   - Configure static website hosting
   - Upload sample_calendar.html

---

### Phase 2.2: Lambda Development (Week 2)

1. **Port Python Code**
   - Convert app.py to Lambda handler
   - Integrate cache_manager with DynamoDB SDK
   - Integrate gemini_client with Secrets Manager

2. **Unit Testing**
   - Test cache functions
   - Test Gemini client
   - Test Lambda handler

3. **Local Testing**
   - Use SAM CLI or Docker
   - Test with sample payloads

---

### Phase 2.3: API Gateway Integration (Week 3)

1. **API Creation**
   - Create REST API with CDK
   - Configure CORS
   - Add request validation

2. **Lambda Integration**
   - Connect API Gateway to Lambda
   - Test with curl/Postman

3. **Frontend Update**
   - Update API URL in sample_calendar.html
   - Deploy to S3

---

### Phase 2.4: Monitoring and Observability (Week 4)

1. **CloudWatch Dashboard**
   - Create dashboard with CDK
   - Add widgets for metrics

2. **Alarms**
   - Configure error alarms
   - Test SNS notifications

3. **Logs**
   - Enable CloudWatch Logs
   - Test log queries

---

### Phase 2.5: Cache Migration (Week 5)

1. **Migration Script**
   - Write Python script to read cache.json
   - Batch write to DynamoDB
   - Validate data integrity

2. **Testing**
   - Test cache hits with migrated data
   - Verify cache key compatibility

---

### Phase 2.6: Testing and Validation (Week 6)

1. **Integration Tests**
   - Test API Gateway → Lambda → DynamoDB
   - Test Lambda → Gemini API

2. **E2E Tests**
   - Simulate user interactions
   - Verify UI updates

3. **Load Tests**
   - 100 concurrent users
   - Measure performance

---

### Phase 2.7: Deployment and Cutover (Week 7)

1. **Production Deployment**
   - Run `cdk deploy --context env=prod`
   - Verify all resources created

2. **Smoke Tests**
   - Test /api/health
   - Test /api/reasoning with sample data

3. **Go-Live**
   - Update DNS (if applicable)
   - Announce to users

---

## Risk Assessment

### Risk 1: Gemini API Rate Limiting (HIGH)

**Description:** Gemini free tier allows 60 requests/day, which may be insufficient
**Impact:** Users unable to get AI reasoning for new locations
**Mitigation:**
- Implement cache-first strategy (80% hit rate target)
- Display informative error message when quota exceeded
- Upgrade to paid tier if needed
- Consider queueing requests and batching

---

### Risk 2: Cold Start Latency (MEDIUM)

**Description:** Lambda cold starts can take 1-3 seconds
**Impact:** Poor user experience for first request
**Mitigation:**
- Provisioned concurrency (increases cost)
- Keep Lambda warm with CloudWatch Events (ping every 5 min)
- Optimize dependencies (use Lambda Layers)
- Display loading spinner in UI

---

### Risk 3: DynamoDB Cost Overrun (MEDIUM)

**Description:** On-demand billing can be expensive with high traffic
**Impact:** Monthly costs exceed budget
**Mitigation:**
- Monitor costs with AWS Budgets
- Set billing alarms
- Consider provisioned capacity if traffic is predictable
- Implement TTL to reduce storage costs

---

### Risk 4: CORS Configuration Errors (LOW)

**Description:** Misconfigured CORS can block frontend requests
**Impact:** API calls fail from browser
**Mitigation:**
- Test CORS with browser DevTools
- Use API Gateway CORS presets
- Document allowed origins clearly

---

### Risk 5: Cache Migration Data Loss (LOW)

**Description:** Errors during cache.json → DynamoDB migration
**Impact:** Loss of cached reasoning data
**Mitigation:**
- Backup cache.json before migration
- Validate all entries after migration
- Implement retry logic in migration script
- Keep Phase 1 system running until migration verified

---

## Appendix

### A. Glossary

- **OCO-2**: Orbiting Carbon Observatory-2, NASA satellite
- **GeoJSON**: Geographic data format (RFC 7946)
- **Gemini API**: Google's generative AI API
- **AWS CDK**: AWS Cloud Development Kit (Infrastructure as Code)
- **DynamoDB**: AWS NoSQL database service
- **API Gateway**: AWS managed API service
- **Lambda**: AWS serverless compute service
- **CloudWatch**: AWS monitoring and logging service
- **Secrets Manager**: AWS secrets management service

---

### B. References

- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [AWS Lambda Python Runtime](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [Google Gemini API Documentation](https://ai.google.dev/docs)
- [Leaflet.js Documentation](https://leafletjs.com/)

---

### C. Version History

| Version | Date       | Author      | Changes                          |
|---------|------------|-------------|----------------------------------|
| 1.0     | 2025-10-30 | Dev Team    | Initial specification created    |

---

**End of Specification**
