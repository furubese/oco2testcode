# AWS CDK Migration Specification

**Project**: CO₂ Anomaly Analysis System
**Specification ID**: 001-aws-cdk-migration
**Version**: 1.0
**Status**: Planning
**Created**: 2025-10-30
**Author**: Development Team

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Project Overview](#project-overview)
3. [Architecture Documentation](#architecture-documentation)
4. [Migration Phases](#migration-phases)
5. [Technical Requirements](#technical-requirements)
6. [Implementation Plan](#implementation-plan)
7. [Risk Assessment](#risk-assessment)
8. [Success Metrics](#success-metrics)
9. [Appendices](#appendices)

---

## Executive Summary

This specification outlines the migration of the CO₂ Anomaly Analysis System from a local Flask-based prototype (Phase 1) to a production-ready AWS serverless architecture (Phase 2) using AWS CDK for infrastructure as code.

### Key Objectives

- **Scalability**: Support 100+ concurrent users (vs. current ~10-20)
- **Reliability**: Achieve 99.9% uptime with multi-AZ deployment
- **Security**: Implement API authentication, WAF protection, and secrets management
- **Cost Efficiency**: Pay-per-use model (~$25-55/month for moderate usage)
- **Maintainability**: Infrastructure as Code with AWS CDK
- **Observability**: Comprehensive monitoring with CloudWatch and X-Ray

### Migration Timeline

- **Total Duration**: 4-6 weeks
- **Phase 1 Documentation**: Complete (this spec)
- **Phase 2 Implementation**: 2-3 weeks
- **Testing & Validation**: 1 week
- **Deployment & Cutover**: 1 week

### Cost Impact

- **Current (Phase 1)**: $0/month (local hosting)
- **Target (Phase 2)**: $25-55/month (AWS serverless)
- **ROI**: Improved reliability, scalability, and professional deployment

---

## Project Overview

### Background

The CO₂ Anomaly Analysis System is a web application that visualizes CO₂ concentration anomalies from OCO-2 satellite data and uses Google Gemini AI to generate reasoning about the causes of these anomalies.

**Current State (Phase 1)**:
- Local Flask server running on port 5000
- File-based caching (cache.json)
- Manual server management
- No authentication or monitoring
- Single point of failure

**Target State (Phase 2)**:
- AWS serverless architecture
- DynamoDB caching with TTL
- API Gateway with authentication
- CloudFront CDN for global distribution
- Comprehensive monitoring and alerts

### Scope

**In Scope**:
- Migration of all backend logic to AWS Lambda
- Conversion of cache.json to DynamoDB
- Static website hosting on S3 + CloudFront
- API Gateway with authentication
- Secrets management with AWS Secrets Manager
- Monitoring with CloudWatch and X-Ray
- Infrastructure as Code with CDK (TypeScript)

**Out of Scope**:
- Changes to core business logic
- Frontend UI redesign
- Gemini API replacement
- Multi-region deployment (Phase 3 consideration)
- Custom domain setup (optional)

### Stakeholders

- **Development Team**: Implementation and testing
- **Operations Team**: Deployment and monitoring
- **End Users**: Researchers and analysts using the system
- **AWS Account Admin**: Resource provisioning and cost management

---

## Architecture Documentation

This specification includes detailed architecture diagrams and documentation organized as follows:

### 📄 [Phase 1 Architecture](./diagrams/phase1-architecture.md)

Current local architecture with Flask server.

**Key Sections**:
- High-level architecture diagram
- Component details (Flask, cache_manager, gemini_client)
- Request flow (static content, API reasoning)
- Technology stack
- Limitations and performance characteristics

**Preview**:
```
Browser → Flask → cache_manager → cache.json
                → gemini_client → Gemini API
```

---

### 📄 [Phase 2 Architecture](./diagrams/phase2-architecture.md)

Target AWS serverless architecture.

**Key Sections**:
- High-level architecture diagram with all AWS services
- Component details for each service
- Edge Layer: CloudFront
- API Layer: API Gateway + WAF
- Compute Layer: Lambda + Lambda Layers
- Data Layer: DynamoDB + S3
- Security Layer: Secrets Manager, IAM
- Monitoring Layer: CloudWatch, X-Ray, SNS
- Request flow diagrams
- Cost estimates (~$25-55/month)
- Advantages over Phase 1

**Preview**:
```
Browser → CloudFront → API Gateway → Lambda → DynamoDB
                     ↓              ↓        ↓ (miss)
                   S3 Static    Secrets Mgr  Gemini API
                   S3 Data
```

---

### 📄 [CDK Stack Structure](./diagrams/cdk-stack-structure.md)

Infrastructure as Code organization with AWS CDK.

**Key Sections**:
- Stack dependency diagram
- Deployment order (BaseStack → StorageStack → LambdaStack → ApiStack → FrontendStack → ObservabilityStack)
- Detailed stack descriptions:
  - **BaseStack**: IAM roles, Secrets Manager, SSM parameters
  - **StorageStack**: DynamoDB table, S3 buckets
  - **LambdaStack**: Lambda function, Lambda layer
  - **ApiStack**: API Gateway, WAF rules
  - **FrontendStack**: S3 static hosting, CloudFront distribution
  - **ObservabilityStack**: CloudWatch alarms, SNS topics
- Cross-stack references and exports
- CDK commands for deployment
- Environment-specific configuration
- Testing strategies

**Preview**:
```
BaseStack (Layer 1)
    ↓
StorageStack (Layer 2)
    ↓
LambdaStack (Layer 3)
    ↓
ApiStack (Layer 4)
    ↓
FrontendStack (Layer 5)
    ↓
ObservabilityStack (Layer 6)
```

---

### 📄 [Data Flow Diagrams](./diagrams/data-flow.md)

Detailed request/response flows for cache hit and cache miss scenarios.

**Key Sections**:
- **Phase 1 Data Flows**:
  - Cache hit scenario (50-100ms)
  - Cache miss scenario (2-6s)
- **Phase 2 Data Flows**:
  - Cache hit scenario (100-200ms)
  - Cache miss scenario (3-6s)
- Cache key generation (SHA256 hashing)
- Cache TTL flow (DynamoDB automatic expiration)
- Error handling flows for both phases
- Performance comparison tables
- Cost per request analysis

**Preview - Cache Hit**:
```
Phase 1: Browser → Flask → cache.json (50-100ms)
Phase 2: Browser → CloudFront → API Gateway → Lambda → DynamoDB (100-200ms)
```

**Preview - Cache Miss**:
```
Phase 1: Browser → Flask → Gemini API → cache.json → Response (2-6s)
Phase 2: Browser → CF → APIGW → Lambda → Secrets Mgr → Gemini API → DynamoDB → Response (3-6s)
```

---

### 📄 [Component Interactions](./diagrams/component-interactions.md)

How components communicate with each other.

**Key Sections**:
- **Phase 1 Component Interaction**:
  - High-level component diagram
  - Module dependencies
  - Communication patterns (cache-aside pattern)
- **Phase 2 Component Interaction**:
  - High-level component diagram with all AWS services
  - Lambda function internal flow
  - AWS service interaction sequences
  - CDK component relationships
- Communication matrices (Phase 1 vs Phase 2)
- Integration points and migration mapping
- Component lifecycle (cold start, warm invocation)

**Preview**:
```
Phase 1: HTML → Flask → Business Logic → Data Layer → External APIs
Phase 2: Browser → CloudFront → API Gateway → Lambda → Multiple AWS Services → Gemini API
```

---

## Migration Phases

### Phase 0: Pre-Migration (1 week)

**Objectives**:
- Complete architecture documentation (this spec)
- Set up AWS account and CDK environment
- Create backup of current system
- Establish baseline metrics

**Tasks**:
1. Review and finalize architecture diagrams
2. Set up AWS account with appropriate billing alerts
3. Install and configure AWS CDK CLI
4. Bootstrap CDK in target AWS region
5. Document current system performance metrics
6. Create backup of cache.json and GeoJSON files
7. Export environment variables from .env

**Deliverables**:
- ✅ Architecture specification (this document)
- ✅ AWS account configured
- ✅ CDK environment ready
- ✅ Baseline metrics documented

---

### Phase 1: Foundation Infrastructure (Week 1)

**Objective**: Deploy base infrastructure (IAM, secrets, parameters).

**Tasks**:
1. Create CDK TypeScript project structure
2. Implement BaseStack:
   - IAM roles for Lambda execution
   - Secrets Manager secret for Gemini API key
   - SSM parameters for configuration
3. Deploy BaseStack to AWS
4. Validate secret storage and retrieval
5. Test IAM role permissions

**Deliverables**:
- CDK project initialized
- BaseStack deployed and tested
- Secrets securely stored

**Validation**:
```bash
# Test secret retrieval
aws secretsmanager get-secret-value --secret-id <secret-name>

# Test parameter retrieval
aws ssm get-parameter --name /app/gemini-model
```

---

### Phase 2: Data Layer (Week 1-2)

**Objective**: Deploy data storage (DynamoDB, S3).

**Tasks**:
1. Implement StorageStack:
   - DynamoDB table with TTL
   - S3 bucket for GeoJSON data
   - S3 bucket for static website
2. Migrate data from cache.json to DynamoDB:
   - Write migration script
   - Transform JSON to DynamoDB items
   - Add TTL attributes
3. Upload GeoJSON files to S3
4. Deploy StorageStack
5. Validate data migration

**Deliverables**:
- StorageStack deployed
- DynamoDB table populated
- GeoJSON files in S3

**Migration Script**:
```python
# migrate_cache.py
import json
import boto3
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('CO2ReasoningCache')

with open('cache.json', 'r') as f:
    cache_data = json.load(f)

for cache_key, entry in cache_data.items():
    # Add TTL (90 days from now)
    ttl = int((datetime.now() + timedelta(days=90)).timestamp())

    item = {
        'cache_key': cache_key,
        'reasoning': entry['reasoning'],
        'cached_at': entry.get('cached_at', datetime.now().isoformat()),
        'metadata': entry.get('metadata', {}),
        'ttl': ttl
    }

    table.put_item(Item=item)
    print(f"Migrated: {cache_key}")
```

---

### Phase 3: Compute Layer (Week 2)

**Objective**: Deploy Lambda function with dependencies.

**Tasks**:
1. Create Lambda layer with dependencies:
   - google-generativeai
   - boto3
2. Convert Flask logic to Lambda handler:
   - Extract reasoning logic from app.py
   - Implement Lambda event parsing
   - Add DynamoDB integration
   - Add Secrets Manager integration
3. Implement LambdaStack
4. Deploy LambdaStack
5. Test Lambda function directly

**Deliverables**:
- Lambda layer built
- Lambda function deployed
- Unit tests passing

**Lambda Handler Structure**:
```python
# lambda_handler.py
import json
import boto3
import hashlib
from datetime import datetime, timedelta
import google.generativeai as genai

dynamodb = boto3.resource('dynamodb')
secrets_client = boto3.client('secretsmanager')
table = dynamodb.Table(os.environ['DYNAMODB_TABLE_NAME'])

def lambda_handler(event, context):
    try:
        # Parse request
        body = json.loads(event['body'])
        lat = body['lat']
        lon = body['lon']
        # ... other parameters

        # Generate cache key
        cache_key = generate_cache_key(lat, lon, date)

        # Check cache
        response = table.get_item(Key={'cache_key': cache_key})
        if 'Item' in response:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'reasoning': response['Item']['reasoning'],
                    'cached': True
                })
            }

        # Cache miss - call Gemini API
        api_key = get_api_key()
        reasoning = call_gemini_api(api_key, lat, lon, co2, ...)

        # Save to cache
        ttl = int((datetime.now() + timedelta(days=90)).timestamp())
        table.put_item(Item={
            'cache_key': cache_key,
            'reasoning': reasoning,
            'cached_at': datetime.now().isoformat(),
            'metadata': {...},
            'ttl': ttl
        })

        return {
            'statusCode': 200,
            'body': json.dumps({
                'reasoning': reasoning,
                'cached': False
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

---

### Phase 4: API Layer (Week 2-3)

**Objective**: Deploy API Gateway with authentication.

**Tasks**:
1. Implement ApiStack:
   - API Gateway REST API
   - API Key and Usage Plan
   - WAF rules
   - Lambda integration
2. Configure CORS
3. Deploy ApiStack
4. Test API endpoints with Postman/curl

**Deliverables**:
- API Gateway deployed
- API key generated
- WAF rules active
- Integration tests passing

**API Testing**:
```bash
# Test health endpoint
curl -X GET https://<api-id>.execute-api.us-east-1.amazonaws.com/prod/health

# Test reasoning endpoint
curl -X POST https://<api-id>.execute-api.us-east-1.amazonaws.com/prod/reasoning \
  -H "x-api-key: <api-key>" \
  -H "Content-Type: application/json" \
  -d '{
    "lat": 35.6762,
    "lon": 139.6503,
    "co2": 420.5,
    "deviation": 5.2,
    "date": "2023-01-15",
    "severity": "high",
    "zscore": 2.8
  }'
```

---

### Phase 5: Frontend Layer (Week 3)

**Objective**: Deploy static website with CloudFront.

**Tasks**:
1. Update sample_calendar.html:
   - Replace API endpoint URL
   - Update to use API key (via CloudFront header)
2. Implement FrontendStack:
   - S3 static website bucket
   - CloudFront distribution
   - Origin Access Identity
3. Upload static files to S3
4. Deploy FrontendStack
5. Test website end-to-end

**Deliverables**:
- Static website deployed
- CloudFront distribution active
- End-to-end testing complete

**Frontend Changes**:
```javascript
// sample_calendar.html - Update API endpoint
const API_ENDPOINT = 'https://d1234567890.cloudfront.net/api/reasoning';
const API_KEY = '<api-key>'; // In production, use CloudFront to inject

async function fetchReasoning(lat, lon, co2, date) {
    const response = await fetch(API_ENDPOINT, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'x-api-key': API_KEY
        },
        body: JSON.stringify({
            lat, lon, co2,
            deviation, date, severity, zscore
        })
    });
    return response.json();
}
```

---

### Phase 6: Monitoring & Observability (Week 3-4)

**Objective**: Deploy monitoring, logging, and alerting.

**Tasks**:
1. Implement ObservabilityStack:
   - CloudWatch dashboard
   - CloudWatch Alarms
   - SNS topic for alerts
2. Configure alarm thresholds
3. Set up email subscriptions
4. Test alarm triggering
5. Create runbooks for common issues

**Deliverables**:
- CloudWatch dashboard deployed
- Alarms configured and tested
- Alert notifications working
- Runbooks documented

**Alarm Definitions**:
```typescript
// ObservabilityStack.ts
new cloudwatch.Alarm(this, 'LambdaErrorRateAlarm', {
  metric: lambdaFunction.metricErrors({
    statistic: 'Sum',
    period: Duration.minutes(5)
  }),
  threshold: 5,
  evaluationPeriods: 1,
  alarmDescription: 'Lambda error rate > 5%',
  actionsEnabled: true
});

new cloudwatch.Alarm(this, 'ApiGateway5xxAlarm', {
  metric: api.metricServerError({
    statistic: 'Sum',
    period: Duration.minutes(5)
  }),
  threshold: 10,
  evaluationPeriods: 1,
  alarmDescription: 'API Gateway 5xx errors > 10 in 5 min'
});
```

---

### Phase 7: Testing & Validation (Week 4)

**Objective**: Comprehensive testing of the entire system.

**Tasks**:
1. **Functional Testing**:
   - Test all API endpoints
   - Verify cache hit/miss behavior
   - Test error handling
2. **Performance Testing**:
   - Load testing with JMeter/Artillery
   - Measure latency (cache hit/miss)
   - Test concurrent users
3. **Security Testing**:
   - Verify API key authentication
   - Test WAF rules
   - Check IAM permissions
4. **Integration Testing**:
   - End-to-end user flows
   - Verify GeoJSON loading
   - Test map interactions
5. **Monitoring Testing**:
   - Trigger alarms intentionally
   - Verify SNS notifications
   - Check CloudWatch dashboards

**Deliverables**:
- Test plan executed
- All tests passing
- Performance benchmarks documented
- Security audit complete

**Performance Test Script**:
```bash
# artillery load test
artillery quick --count 100 --num 10 https://<cloudfront-url>/api/reasoning
```

---

### Phase 8: Deployment & Cutover (Week 4-5)

**Objective**: Go live with Phase 2 architecture.

**Tasks**:
1. **Pre-Cutover**:
   - Final backup of Phase 1 system
   - Document rollback procedure
   - Create deployment checklist
2. **Cutover**:
   - Update DNS (if using custom domain)
   - Monitor for 24 hours
   - Keep Phase 1 running as backup
3. **Post-Cutover**:
   - Monitor CloudWatch dashboards
   - Verify user access
   - Collect user feedback
4. **Decommission Phase 1**:
   - Stop Flask server (after 1 week of stability)
   - Archive Phase 1 code and data
   - Document lessons learned

**Deliverables**:
- Phase 2 live in production
- Phase 1 decommissioned
- Post-mortem document

**Rollback Plan**:
If critical issues arise:
1. Revert DNS to Phase 1 server
2. Restart Flask server
3. Investigate and fix Phase 2 issues
4. Re-test before second cutover attempt

---

## Technical Requirements

### Functional Requirements

| ID | Requirement | Phase 1 | Phase 2 | Priority |
|----|-------------|---------|---------|----------|
| FR-1 | Display CO₂ anomaly map | ✅ | ✅ | High |
| FR-2 | Time-series data selection | ✅ | ✅ | High |
| FR-3 | Generate AI reasoning for anomalies | ✅ | ✅ | High |
| FR-4 | Cache reasoning results | ✅ | ✅ | High |
| FR-5 | Serve GeoJSON data | ✅ | ✅ | High |
| FR-6 | API authentication | ❌ | ✅ | Medium |
| FR-7 | Rate limiting | ❌ | ✅ | Medium |
| FR-8 | Monitoring and alerts | ❌ | ✅ | Medium |

### Non-Functional Requirements

| ID | Requirement | Phase 1 | Phase 2 | Target |
|----|-------------|---------|---------|--------|
| NFR-1 | Response time (cache hit) | 50-100ms | 100-200ms | <300ms |
| NFR-2 | Response time (cache miss) | 2-6s | 3-6s | <10s |
| NFR-3 | Concurrent users | 10-20 | 100+ | 100+ |
| NFR-4 | Availability | ~95% | 99.9% | 99.9% |
| NFR-5 | Data persistence | File-based | Multi-AZ | Durable |
| NFR-6 | Cost | $0 | $25-55/mo | <$100/mo |

### Security Requirements

| ID | Requirement | Phase 2 Implementation |
|----|-------------|----------------------|
| SEC-1 | API authentication | API Gateway API Keys |
| SEC-2 | Secrets management | AWS Secrets Manager |
| SEC-3 | Encryption at rest | DynamoDB encryption, S3 encryption |
| SEC-4 | Encryption in transit | HTTPS everywhere (CloudFront, API Gateway) |
| SEC-5 | Rate limiting | WAF rules (2000 req/5min per IP) |
| SEC-6 | DDoS protection | AWS Shield (standard), WAF |
| SEC-7 | Least privilege access | IAM roles with minimal permissions |
| SEC-8 | Audit logging | CloudWatch Logs, X-Ray tracing |

### Compliance Requirements

| ID | Requirement | Implementation |
|----|-------------|----------------|
| COMP-1 | Data residency | Deploy in compliant AWS region (e.g., us-east-1) |
| COMP-2 | Data retention | DynamoDB TTL (90 days), S3 lifecycle policies |
| COMP-3 | Audit trails | CloudWatch Logs retention (14 days minimum) |
| COMP-4 | Access control | IAM policies, API keys |

---

## Implementation Plan

### Technology Stack

#### Phase 2 Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Frontend** | HTML/CSS/JS | - | Static web application |
| | Leaflet.js | 1.9.4 | Interactive mapping |
| **CDN** | CloudFront | - | Content delivery, caching |
| **API** | API Gateway | REST | HTTP API endpoints |
| | AWS WAF | - | Security filtering |
| **Compute** | Lambda | Python 3.11 | Serverless functions |
| **Data** | DynamoDB | - | NoSQL cache storage |
| | S3 | - | Static files, GeoJSON data |
| **Security** | Secrets Manager | - | API key storage |
| | IAM | - | Access control |
| **Monitoring** | CloudWatch | - | Logs, metrics, alarms |
| | X-Ray | - | Distributed tracing |
| | SNS | - | Alert notifications |
| **IaC** | AWS CDK | TypeScript | Infrastructure as Code |
| **AI** | Gemini API | 2.0-flash-exp | Reasoning generation |

### CDK Project Structure

```
cdk/
├── bin/
│   └── co2-analysis-app.ts          # CDK app entry point
├── lib/
│   ├── base-stack.ts                # IAM, Secrets, SSM
│   ├── storage-stack.ts             # DynamoDB, S3
│   ├── lambda-stack.ts              # Lambda function, layer
│   ├── api-stack.ts                 # API Gateway, WAF
│   ├── frontend-stack.ts            # S3 static, CloudFront
│   └── observability-stack.ts       # CloudWatch, SNS
├── lambda/
│   ├── reasoning-handler/
│   │   ├── index.py                 # Lambda handler
│   │   ├── cache_manager.py         # DynamoDB cache logic
│   │   ├── gemini_client.py         # Gemini API client
│   │   └── requirements.txt         # Python dependencies
│   └── layers/
│       └── dependencies/
│           └── requirements.txt     # Layer dependencies
├── test/
│   ├── base-stack.test.ts
│   ├── storage-stack.test.ts
│   └── ...
├── cdk.json                         # CDK configuration
├── package.json                     # Node.js dependencies
└── tsconfig.json                    # TypeScript config
```

### Environment Configuration

```json
// cdk.json
{
  "app": "npx ts-node bin/co2-analysis-app.ts",
  "context": {
    "dev": {
      "account": "111111111111",
      "region": "us-east-1",
      "provisionedConcurrency": 0,
      "wafEnabled": false
    },
    "prod": {
      "account": "222222222222",
      "region": "us-east-1",
      "provisionedConcurrency": 1,
      "wafEnabled": true
    }
  }
}
```

---

## Risk Assessment

### High Risk

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Data Loss During Migration** | High | Low | Create backups before migration, validate data after migration, keep Phase 1 running as backup |
| **Gemini API Key Exposure** | High | Low | Use Secrets Manager, never commit keys to Git, rotate keys after migration |
| **Cost Overrun** | High | Medium | Set up billing alarms, use cost explorer, implement throttling |

### Medium Risk

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Performance Degradation** | Medium | Medium | Load testing before cutover, provisioned concurrency for Lambda, CloudFront caching |
| **Lambda Cold Starts** | Medium | High | Provisioned concurrency (1 instance), optimize function size, keep functions warm |
| **DynamoDB Throttling** | Medium | Low | Use on-demand billing mode, implement exponential backoff |

### Low Risk

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **CDK Deployment Failure** | Low | Low | Use `cdk diff` before deploy, test in dev environment first |
| **CloudFront Propagation Delay** | Low | High | Plan for 15-20 min CloudFront deployment time, test before cutover |
| **IAM Permission Issues** | Low | Medium | Use managed policies where possible, test permissions thoroughly |

---

## Success Metrics

### Performance Metrics

| Metric | Baseline (Phase 1) | Target (Phase 2) | Measurement Method |
|--------|-------------------|------------------|-------------------|
| Cache Hit Latency | 50-100ms | <300ms | CloudWatch metrics |
| Cache Miss Latency | 2-6s | <10s | CloudWatch metrics |
| Concurrent Users | 10-20 | 100+ | Load testing |
| Availability | ~95% | 99.9% | CloudWatch uptime |
| Error Rate | Unknown | <1% | CloudWatch metrics |

### Cost Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Monthly Cost | $25-55 | AWS Cost Explorer |
| Cost per Request (cached) | <$0.00001 | CloudWatch + Cost Explorer |
| Cost per Request (uncached) | <$0.00005 | CloudWatch + Cost Explorer |

### Business Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| User Satisfaction | >80% | User survey |
| Time to Deploy Updates | <1 hour | CDK deployment time |
| Mean Time to Detect Issues | <5 minutes | CloudWatch Alarms |
| Mean Time to Resolve Issues | <1 hour | Incident tracking |

---

## Appendices

### Appendix A: Glossary

| Term | Definition |
|------|------------|
| **CDK** | AWS Cloud Development Kit - Infrastructure as Code framework |
| **CloudFront** | AWS Content Delivery Network (CDN) |
| **DynamoDB** | AWS NoSQL database service |
| **Lambda** | AWS serverless compute service |
| **API Gateway** | AWS managed API service |
| **WAF** | Web Application Firewall |
| **OAI** | Origin Access Identity - CloudFront authentication for S3 |
| **TTL** | Time To Live - automatic expiration of data |
| **SNS** | Simple Notification Service - pub/sub messaging |
| **X-Ray** | AWS distributed tracing service |

### Appendix B: References

1. [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
2. [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
3. [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
4. [API Gateway Documentation](https://docs.aws.amazon.com/apigateway/)
5. [CloudFront Documentation](https://docs.aws.amazon.com/cloudfront/)

### Appendix C: Diagram Index

All diagrams are located in `./diagrams/` and are written in Mermaid format for easy rendering in GitHub and documentation tools.

| Diagram | File | Description |
|---------|------|-------------|
| Phase 1 Architecture | [phase1-architecture.md](./diagrams/phase1-architecture.md) | Current local Flask architecture |
| Phase 2 Architecture | [phase2-architecture.md](./diagrams/phase2-architecture.md) | Target AWS serverless architecture |
| CDK Stack Structure | [cdk-stack-structure.md](./diagrams/cdk-stack-structure.md) | CDK stacks and dependencies |
| Data Flow | [data-flow.md](./diagrams/data-flow.md) | Request/response flows with cache scenarios |
| Component Interactions | [component-interactions.md](./diagrams/component-interactions.md) | How components communicate |

### Appendix D: Contact Information

| Role | Name | Email |
|------|------|-------|
| Project Lead | TBD | tbd@example.com |
| AWS Architect | TBD | tbd@example.com |
| DevOps Engineer | TBD | tbd@example.com |

### Appendix E: Change Log

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-10-30 | 1.0 | Initial specification created | Development Team |

---

## Approval

This specification requires approval from the following stakeholders:

| Stakeholder | Role | Signature | Date |
|-------------|------|-----------|------|
| TBD | Project Lead | | |
| TBD | AWS Architect | | |
| TBD | Security Lead | | |

---

**End of Specification**
