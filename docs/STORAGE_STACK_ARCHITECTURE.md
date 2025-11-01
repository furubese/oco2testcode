# StorageStack Architecture

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            StorageStack (Layer 3)                            │
│                         Data Persistence & Storage                           │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────┐
│   AWS Systems Manager   │
│   Parameter Store       │
├─────────────────────────┤
│ /co2-analysis/{env}/    │
│   storage/              │
│   ├── dynamodb/         │
│   │   ├── cache-table-* │
│   │   └── stream-arn    │
│   ├── s3/               │
│   │   ├── static-*      │
│   │   └── geojson-*     │
│   └── cloudfront/       │
│       └── oai-id        │
└─────────────────────────┘
           │
           │ Runtime Discovery
           ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    DynamoDB Cache Table                             │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │  Partition Key: cache_key (String)                                  │    │
│  │  TTL Attribute: ttl (Number) - 90 days                             │    │
│  │                                                                      │    │
│  │  ┌────────────────────────────────────────────────────────────┐    │    │
│  │  │ Global Secondary Index: cached-at-index                    │    │    │
│  │  │ Partition Key: cached_at (String)                          │    │    │
│  │  │ Projection: ALL                                            │    │    │
│  │  └────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  │  Features:                                                          │    │
│  │  • Billing Mode: PAY_PER_REQUEST (dev/staging)                     │    │
│  │                  PROVISIONED (prod: 5 RCU/5 WCU)                   │    │
│  │  • Encryption: AWS Managed Keys                                    │    │
│  │  • Streams: NEW_AND_OLD_IMAGES                                     │    │
│  │  • Point-in-time Recovery: Enabled (prod only)                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                         │                                                     │
│                         │ DynamoDB Streams                                    │
│                         ▼                                                     │
│             (Future: CDC, Analytics, Replication)                            │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                               │
│  ┌─────────────────────────────┐      ┌─────────────────────────────┐       │
│  │  S3: Static Website Bucket  │      │   S3: GeoJSON Data Bucket   │       │
│  ├─────────────────────────────┤      ├─────────────────────────────┤       │
│  │ • HTML, CSS, JavaScript     │      │ • CO₂ observation data      │       │
│  │ • CloudFront origin         │      │ • GeoJSON format            │       │
│  │ • Block public access       │      │ • CORS enabled              │       │
│  │ • S3-managed encryption     │      │ • Block public access       │       │
│  │ • SSL/TLS enforced          │      │ • S3-managed encryption     │       │
│  │ • Versioned (prod only)     │      │ • SSL/TLS enforced          │       │
│  └─────────────────────────────┘      └─────────────────────────────┘       │
│              │                                      │                         │
│              │                                      │                         │
│              │         ┌────────────────┐          │                         │
│              └────────▶│ CloudFront OAI │◀─────────┘                         │
│                        ├────────────────┤                                    │
│                        │ Secure Access  │                                    │
│                        │ to S3 Buckets  │                                    │
│                        └────────────────┘                                    │
│                                │                                              │
│                                │ Read Permissions                             │
│                                ▼                                              │
│                     (Used by FrontendStack)                                  │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                        Stack Dependencies                                     │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌──────────────┐                                                            │
│  │  BaseStack   │ (Layer 1)                                                  │
│  └──────┬───────┘                                                            │
│         │ Provides: Naming conventions, tagging patterns                     │
│         ▼                                                                     │
│  ┌──────────────┐                                                            │
│  │StorageStack  │ (Layer 3) ◀── YOU ARE HERE                                │
│  └──────┬───────┘                                                            │
│         │                                                                     │
│         ├─────▶ ComputeStack (Layer 4)                                       │
│         │       Exports: cacheTable                                          │
│         │       Grants: Read/Write permissions to Lambda                     │
│         │                                                                     │
│         ├─────▶ FrontendStack (Layer 5)                                      │
│         │       Exports: staticWebsiteBucket, geoJsonBucket, OAI             │
│         │       Used by: CloudFront distribution                             │
│         │                                                                     │
│         └─────▶ MonitoringStack (Layer 6)                                    │
│                 Exports: cacheTable                                          │
│                 Used by: CloudWatch alarms (throttling, errors)              │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Write Path (Caching):
```
┌─────────────┐
│   Lambda    │
│  Function   │
└──────┬──────┘
       │
       │ 1. Generate cache key from query params
       │
       ▼
┌──────────────────────────────────────┐
│ Check if cache_key exists in table   │
└──────┬───────────────────────────────┘
       │
       │ 2. If not found, call Gemini API
       │
       ▼
┌──────────────────────────────────────┐
│ Store result in DynamoDB              │
│ • cache_key: hash(query_params)      │
│ • cached_at: ISO timestamp           │
│ • ttl: now + 90 days (Unix)          │
│ • reasoning_result: Gemini response  │
│ • query_params: original params      │
└──────────────────────────────────────┘
       │
       │ 3. TTL automatically deletes after 90 days
       │
       ▼
┌──────────────────────────────────────┐
│ Return cached or fresh result        │
└──────────────────────────────────────┘
```

### Read Path (Cache Hit):
```
┌─────────────┐
│   Lambda    │
│  Function   │
└──────┬──────┘
       │
       │ 1. Generate cache key from query params
       │
       ▼
┌──────────────────────────────────────┐
│ Query DynamoDB by cache_key          │
└──────┬───────────────────────────────┘
       │
       │ 2. Cache hit!
       │
       ▼
┌──────────────────────────────────────┐
│ Check if TTL has expired             │
│ (DynamoDB handles this automatically)│
└──────┬───────────────────────────────┘
       │
       │ 3. Return cached result
       │
       ▼
┌──────────────────────────────────────┐
│ Return to client with cache metadata │
└──────────────────────────────────────┘
```

## Security Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         Security Controls                                     │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────┐
│   IAM Permissions   │
├─────────────────────┤
│ Lambda Execution    │
│ Role                │
│  ├─ DynamoDB:       │
│  │  ├─ GetItem     │
│  │  ├─ PutItem     │
│  │  ├─ Query       │
│  │  └─ UpdateItem  │
│  │                  │
│  ├─ SSM:            │
│  │  ├─ GetParameter │
│  │  └─ GetParameters│
│  │                  │
│  └─ CloudWatch:     │
│     └─ Logs         │
└─────────────────────┘

┌─────────────────────┐
│  Data Encryption    │
├─────────────────────┤
│ At Rest:            │
│ • DynamoDB: AWS KMS │
│ • S3: AES-256       │
│                     │
│ In Transit:         │
│ • TLS 1.2+          │
│ • HTTPS required    │
└─────────────────────┘

┌─────────────────────┐
│  Access Control     │
├─────────────────────┤
│ S3 Buckets:         │
│ • Block Public      │
│ • OAI only access   │
│ • No direct access  │
│                     │
│ DynamoDB:           │
│ • IAM only          │
│ • No public access  │
└─────────────────────┘

┌─────────────────────┐
│  Data Retention     │
├─────────────────────┤
│ Production:         │
│ • RETAIN policy     │
│ • Versioning on     │
│ • Backups enabled   │
│                     │
│ Dev/Staging:        │
│ • DESTROY policy    │
│ • Auto-delete       │
└─────────────────────┘
```

## Cost Analysis

### DynamoDB Pricing (us-east-1)

#### Development Environment (PAY_PER_REQUEST):
- **Read:** $0.25 per million requests
- **Write:** $1.25 per million requests
- **Storage:** $0.25 per GB/month

**Example Monthly Cost:**
- 1M reads: $0.25
- 100K writes: $0.125
- 1 GB storage: $0.25
- **Total: ~$0.63/month**

#### Production Environment (PROVISIONED):
- **Read capacity:** 5 RCU × $0.00013/hour × 730 hours = $0.47/month
- **Write capacity:** 5 WCU × $0.00065/hour × 730 hours = $2.37/month
- **Storage:** $0.25 per GB/month

**Example Monthly Cost:**
- 5 RCU: $0.47
- 5 WCU: $2.37
- 1 GB storage: $0.25
- **Total: ~$3.09/month**

### S3 Pricing (us-east-1):
- **Storage:** $0.023 per GB/month
- **Requests:**
  - GET: $0.0004 per 1K requests
  - PUT: $0.005 per 1K requests

**Example Monthly Cost:**
- 10 GB storage: $0.23
- 100K GET: $0.04
- **Total: ~$0.27/month**

### Parameter Store:
- **Standard tier:** FREE (up to 10K parameters)

### Total Estimated Monthly Cost:
- **Dev:** ~$0.90/month
- **Prod:** ~$3.36/month (plus CloudWatch costs)

## Performance Characteristics

### DynamoDB:
- **Latency:** Single-digit milliseconds
- **Throughput:**
  - Dev: Unlimited (on-demand)
  - Prod: 5 reads/sec, 5 writes/sec (can be scaled)
- **Consistency:** Eventually consistent reads (configurable)

### S3:
- **Latency:** 100-200ms first byte
- **Throughput:**
  - 3,500 PUT/COPY/POST/DELETE requests per second per prefix
  - 5,500 GET/HEAD requests per second per prefix

### Parameter Store:
- **Latency:** ~10ms
- **Throughput:** 1,000 transactions per second (standard)

## Monitoring & Observability

### CloudWatch Metrics (Automatic):

#### DynamoDB:
- `ConsumedReadCapacityUnits`
- `ConsumedWriteCapacityUnits`
- `UserErrors` (throttling)
- `SystemErrors`
- `SuccessfulRequestLatency`

#### S3:
- `NumberOfObjects`
- `BucketSizeBytes`
- `AllRequests`
- `4xxErrors`
- `5xxErrors`

### Recommended Alarms (MonitoringStack):
1. DynamoDB throttling > 10 errors in 5 minutes
2. DynamoDB latency > 100ms (p99)
3. S3 4xx errors > 5% of requests
4. S3 5xx errors > 0

## Disaster Recovery

### Backup Strategy:

#### DynamoDB:
- **Point-in-time Recovery:** Enabled (production)
- **Restore Window:** Last 35 days
- **Recovery Time Objective (RTO):** < 1 hour
- **Recovery Point Objective (RPO):** < 5 minutes

#### S3:
- **Versioning:** Enabled (production)
- **Cross-Region Replication:** Optional (future)
- **MFA Delete:** Can be enabled for production

### Recovery Procedures:

1. **DynamoDB Table Loss:**
   ```bash
   aws dynamodb restore-table-to-point-in-time \
     --source-table-name co2-analysis-prod-cache \
     --target-table-name co2-analysis-prod-cache-restored \
     --restore-date-time 2025-11-01T12:00:00Z
   ```

2. **S3 Object Deletion:**
   ```bash
   # Restore from version
   aws s3api copy-object \
     --copy-source bucket/key?versionId=xyz \
     --bucket bucket \
     --key key
   ```

## Compliance & Governance

### Data Classification:
- **Sensitivity:** Public (CO₂ data), Low (cached results)
- **Retention:** 90 days (automatic via TTL)
- **Geographic Restrictions:** None (can be added via S3 Object Lock)

### Compliance Controls:
- ✅ Encryption at rest (GDPR, HIPAA, SOC 2)
- ✅ Encryption in transit (PCI-DSS)
- ✅ Access logging available (future enhancement)
- ✅ Data retention controls (TTL)
- ✅ Audit trail (DynamoDB Streams)

## Operational Runbook

### Common Operations:

#### 1. Clear Cache:
```bash
# Clear all cache entries
aws dynamodb scan \
  --table-name co2-analysis-dev-cache \
  --projection-expression cache_key | \
  jq -r '.Items[].cache_key.S' | \
  while read key; do
    aws dynamodb delete-item \
      --table-name co2-analysis-dev-cache \
      --key "{\"cache_key\":{\"S\":\"$key\"}}"
  done
```

#### 2. Query Recent Cache Entries:
```bash
# Query using GSI for items cached in last hour
aws dynamodb query \
  --table-name co2-analysis-dev-cache \
  --index-name cached-at-index \
  --key-condition-expression "cached_at > :one_hour_ago" \
  --expression-attribute-values '{":one_hour_ago":{"S":"2025-11-01T12:00:00Z"}}'
```

#### 3. Monitor Table Size:
```bash
# Get table metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name UserErrors \
  --dimensions Name=TableName,Value=co2-analysis-prod-cache \
  --start-time 2025-11-01T00:00:00Z \
  --end-time 2025-11-01T23:59:59Z \
  --period 3600 \
  --statistics Sum
```

#### 4. Upload Data to S3:
```bash
# Upload GeoJSON file
aws s3 cp data.geojson \
  s3://co2-analysis-dev-geojson-data/observations/2025/11/data.geojson \
  --content-type application/geo+json \
  --cache-control max-age=3600
```

## Future Enhancements Roadmap

### Phase 1 (Next Sprint):
- [ ] Add S3 lifecycle policies for archival
- [ ] Implement DynamoDB auto-scaling
- [ ] Add CloudWatch dashboard

### Phase 2 (Q2):
- [ ] Enable S3 access logging for production
- [ ] Add cross-region replication for DR
- [ ] Implement S3 Intelligent-Tiering

### Phase 3 (Q3):
- [ ] Add DynamoDB global tables for multi-region
- [ ] Implement fine-grained CORS policies
- [ ] Add S3 bucket analytics

### Phase 4 (Q4):
- [ ] Evaluate PartiQL for complex queries
- [ ] Consider DynamoDB Accelerator (DAX)
- [ ] Implement S3 Object Lock for compliance
