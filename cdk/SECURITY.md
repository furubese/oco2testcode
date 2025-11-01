# Security Best Practices - CDK Nag Integration

This document describes the security best practices implemented in the CO2 Anomaly Analysis System CDK infrastructure, including CDK Nag integration and all security controls.

## CDK Nag Integration

CDK Nag is integrated into all stacks to enforce AWS security best practices. The integration runs automatically during `cdk synth` and validates resources against AWS Solutions best practices.

### Configuration

CDK Nag is configured in `bin/co2-analysis-app.ts`:

```typescript
import { AwsSolutionsChecks } from 'cdk-nag';

// Apply AWS Solutions security checks to all stacks
cdk.Aspects.of(app).add(new AwsSolutionsChecks({ verbose: true }));
```

### Running Security Validation

```bash
# Validate all stacks with CDK Nag
cd cdk
npm run build
npx cdk synth --context environment=dev

# The output will show any security violations
# ✅ indicates all checks passed
# ⚠️  indicates warnings
# ❌ indicates errors that must be resolved
```

## Security Controls Implemented

### 1. S3 Bucket Security

**All S3 buckets implement the following security controls:**

✅ **Encryption at Rest**: All buckets use S3-managed encryption (AES-256)
✅ **Block Public Access**: All buckets have `BlockPublicAccess.BLOCK_ALL` enabled
✅ **Enforce TLS/HTTPS**: All buckets enforce SSL/TLS for all operations via `enforceSSL: true`
✅ **Access Logging**: Data buckets log access to a dedicated logs bucket
✅ **Versioning**: Enabled for production environments on critical buckets
✅ **Lifecycle Policies**: Configured for cost optimization and compliance

**Buckets:**
- `AccessLogsBucket` - Stores S3 and CloudFront access logs
- `GeoJsonBucket` - Stores GeoJSON data files
- `StaticWebsiteBucket` - Hosts static website files
- `CloudFrontLogsBucket` - Stores CloudFront distribution logs

**Access Control:**
- CloudFront Origin Access Identity (OAI) is used for S3 access
- No direct public access to buckets
- All access is mediated through CloudFront with HTTPS enforcement

### 2. IAM Security

**Least-Privilege Principle:**

✅ **Lambda Execution Role** (`base-stack.ts:67-77`)
- Uses AWS managed policy `AWSLambdaBasicExecutionRole` for CloudWatch Logs
- Conditionally adds `AWSXRayDaemonWriteAccess` only when X-Ray is enabled
- Grants read-only access to Secrets Manager (Gemini API key)
- Grants read/write access to DynamoDB cache table (scoped to specific table)

**IAM Wildcard Suppression:**
- DynamoDB GSI access requires wildcard (`/index/*`) - properly suppressed with justification
- Wildcard is scoped to specific table ARN following AWS best practices

### 3. Secrets Management

**AWS Secrets Manager:**

✅ **Gemini API Key Secret** (`base-stack.ts:37-60`)
- Encrypted at rest with AWS managed key (`aws/secretsmanager`)
- Retention policy: RETAIN for production, DESTROY for dev/staging
- Access restricted to Lambda execution role only

**Suppression: AwsSolutions-SMG4** (Automatic Rotation)
- **Justification**: Gemini API key is managed externally by Google Cloud Console
- Automatic rotation not applicable for third-party API keys
- Key must be manually rotated through provider and updated in Secrets Manager

### 4. DynamoDB Security

**Cache Table Security:**

✅ **Encryption**: AWS managed encryption enabled
✅ **Point-in-Time Recovery (PITR)**: Enabled for production environment
✅ **On-Demand Billing**: Prevents throttling issues
✅ **TTL Enabled**: Automatic cleanup of expired cache entries
✅ **Access Control**: Least-privilege IAM permissions via Lambda execution role

**Suppression: AwsSolutions-DDB3** (PITR for dev/staging)
- **Justification**: PITR disabled for non-production to reduce costs
- Non-production data can be rebuilt if needed
- Production environment has PITR enabled

### 5. CloudFront Security

**Distribution Security:**

✅ **HTTPS Only**: `ViewerProtocolPolicy.REDIRECT_TO_HTTPS` enforces HTTPS
✅ **TLS 1.2 Minimum**: Configured with `SecurityPolicyProtocol.TLS_V1_2_2021`
✅ **Security Headers**: Custom ResponseHeadersPolicy includes:
- Strict-Transport-Security (HSTS) - 365 days, includeSubdomains, preload
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Referrer-Policy: strict-origin-when-cross-origin

✅ **Access Logging**: All requests logged to dedicated S3 bucket
✅ **Origin Access Identity (OAI)**: Restricts S3 access to CloudFront only
✅ **HTTP/2 and HTTP/3**: Enabled for performance and security

**Suppressions:**

**AwsSolutions-CFR1** (Geo Restrictions)
- **Justification**: CO2 analysis application should be globally accessible
- Public scientific data for research and monitoring purposes
- No regulatory requirement for geo-restrictions

**AwsSolutions-CFR2** (WAF Integration)
- **Justification**: WAF enabled based on environment configuration
- Enabled for staging and production (`wafEnabled: true`)
- Disabled for dev environment to reduce costs
- Dev environments don't handle production traffic or sensitive data

**AwsSolutions-CFR4** (TLS Version with Default Certificate)
- **Justification**: Using default CloudFront domain (*.cloudfront.net)
- Default CloudFront certificate supports TLS 1.0+
- To enforce TLS 1.2+ minimum, custom domain with ACM certificate required
- HTTPS enforced via `REDIRECT_TO_HTTPS` policy
- **Recommendation**: Add custom domain with ACM certificate for stricter TLS requirements

### 6. Lambda Security

**Function Security:**

✅ **Execution Role**: Least-privilege IAM role with minimal permissions
✅ **Reserved Concurrency**: Limits to prevent runaway costs (10 for prod, 5 for dev)
✅ **X-Ray Tracing**: Enabled for staging/prod environments
✅ **CloudWatch Insights**: Enabled for enhanced monitoring
✅ **Environment Variables**: No secrets stored (uses Secrets Manager)
✅ **Log Retention**: Configured based on environment (7/14/30 days)
✅ **Log Encryption**: CloudWatch Logs encrypted with AWS managed key

**Runtime:**
- Python 3.11 (supported, non-deprecated runtime)
- Regularly updated dependencies

**Suppression: AwsSolutions-L1** (Runtime Version)
- **Justification**: Python 3.11 is supported and appropriate for this workload
- Not deprecated, suitable for dependencies

### 7. Network Security

**Data in Transit:**

✅ **All data in transit uses TLS/HTTPS:**
- CloudFront enforces HTTPS (REDIRECT_TO_HTTPS)
- S3 enforces TLS (enforceSSL: true)
- DynamoDB SDK uses HTTPS by default
- Secrets Manager SDK uses HTTPS by default
- Lambda invocations encrypted in transit

**No VPC Required:**
- Current serverless architecture doesn't require VPC
- Lambda functions access AWS services via public endpoints (encrypted)
- Optional VPC configuration available in `network-stack.ts` for future use

### 8. Monitoring and Alerting

**CloudWatch Security Monitoring:**

✅ **Lambda Metrics**: Errors, duration, throttles
✅ **DynamoDB Metrics**: Throttle events, capacity consumption
✅ **Alarms**: SNS notifications for security-relevant events
✅ **Dashboard**: Centralized visibility into system health

**SNS Topic Security:**
✅ **Encryption**: AWS managed key for data at rest
✅ **HTTPS Enforcement**: Policy denies non-TLS publish operations

## Security Suppression Summary

All CDK Nag suppressions have been validated using the `CheckCDKNagSuppressions` tool and include proper justifications.

| Stack | Rule ID | Resource | Justification |
|-------|---------|----------|---------------|
| BaseStack | AwsSolutions-SMG4 | GeminiApiKeySecret | Third-party API key managed externally |
| BaseStack | AwsSolutions-IAM4 | LambdaExecutionRole | AWS managed policies follow best practices |
| BaseStack | AwsSolutions-IAM5 | LambdaExecutionRole | DynamoDB GSI wildcard required |
| StorageStack | AwsSolutions-S1 | AccessLogsBucket | Prevents infinite logging loop |
| StorageStack | AwsSolutions-DDB3 | CacheTable | PITR disabled for non-prod (cost optimization) |
| FrontendStack | AwsSolutions-S1 | CloudFrontLogsBucket | Prevents infinite logging loop |
| FrontendStack | AwsSolutions-CFR1 | Distribution | Global scientific data access |
| FrontendStack | AwsSolutions-CFR2 | Distribution | WAF enabled for prod/staging |
| FrontendStack | AwsSolutions-CFR4 | Distribution | Default CloudFront certificate |
| ComputeStack | AwsSolutions-L1 | ReasoningFunction | Python 3.11 is supported runtime |

## Security Recommendations

### Immediate Actions ✅ COMPLETED
- [x] Enable CDK Nag on all stacks
- [x] Block public access on all S3 buckets
- [x] Enforce TLS/HTTPS for all data in transit
- [x] Implement least-privilege IAM policies
- [x] Enable encryption at rest for all data stores
- [x] Configure access logging for S3 and CloudFront
- [x] Add security headers to CloudFront responses
- [x] Document all CDK Nag suppressions

### Future Enhancements
- [ ] Add custom domain with ACM certificate (enables TLS 1.2+ enforcement)
- [ ] Implement AWS WAF for all environments (currently prod/staging only)
- [ ] Add KMS Customer Managed Keys (CMK) for enhanced encryption control
- [ ] Implement automatic secret rotation for supported secret types
- [ ] Add geo-restrictions if regulatory requirements emerge
- [ ] Implement VPC endpoints if Lambda moves to VPC
- [ ] Add AWS Config rules for continuous compliance monitoring
- [ ] Implement AWS Security Hub for centralized security findings

## Compliance and Audit

### Security Standards
This infrastructure follows AWS Well-Architected Framework Security Pillar:
- **Identity and Access Management**: Least-privilege IAM
- **Detection**: CloudWatch monitoring and alarms
- **Infrastructure Protection**: Network security, encryption
- **Data Protection**: Encryption at rest and in transit
- **Incident Response**: Logging and monitoring

### Audit Trail
- **CloudWatch Logs**: Lambda execution logs (retention: 7-30 days)
- **S3 Access Logs**: All bucket access logged (retention: 90 days)
- **CloudFront Logs**: All distribution requests logged (retention: 90 days)
- **CloudTrail**: AWS API calls (configured separately)

## Security Contacts

For security issues or questions:
- Review this document
- Check CDK Nag output: `npx cdk synth`
- Validate suppressions: Use `CheckCDKNagSuppressions` tool
- Consult AWS Security Best Practices: https://docs.aws.amazon.com/security/

## Version History

- **v1.0** (2025-01-XX) - Initial CDK Nag integration
  - All critical security violations resolved
  - All suppressions documented with justification
  - Security best practices implemented across all stacks
