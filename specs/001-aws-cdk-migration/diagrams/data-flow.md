# Data Flow Diagrams

## Overview

This document shows detailed data flows through the system, focusing on cache hit and cache miss scenarios for both Phase 1 and Phase 2.

---

## Phase 1 - Data Flow (Local)

### Cache Hit Scenario

```mermaid
sequenceDiagram
    participant Browser
    participant Flask as Flask Server
    participant CM as cache_manager.py
    participant CacheFile as cache.json

    Browser->>Flask: POST /api/reasoning<br/>{lat, lon, co2, date...}
    activate Flask

    Flask->>Flask: Validate request parameters
    Flask->>CM: generate_cache_key(lat, lon, date)
    activate CM
    CM->>CM: SHA256(lat_lon_date)
    CM-->>Flask: cache_key
    deactivate CM

    Flask->>CM: get_cached_reasoning(cache_key)
    activate CM
    CM->>CacheFile: load_cache()
    activate CacheFile
    CacheFile-->>CM: JSON data
    deactivate CacheFile

    CM->>CM: Check if cache_key exists
    CM->>CM: Extract reasoning from entry
    CM-->>Flask: reasoning (string)
    deactivate CM

    Flask->>Flask: Build JSON response<br/>{reasoning, cached: true}
    Flask-->>Browser: 200 OK<br/>{reasoning, cached: true, cache_key}
    deactivate Flask

    Note over Browser,CacheFile: Total time: ~50-100ms<br/>No external API call
```

**Steps**:
1. Browser sends POST request with CO2 data
2. Flask validates required fields
3. cache_manager generates SHA256 cache key
4. cache_manager loads cache.json from disk
5. **Cache Hit**: Key found in cache
6. Extract reasoning text from cache entry
7. Return response immediately (cached: true)

**Performance**:
- Latency: 50-100ms
- Bottleneck: Local file I/O
- No external API calls

---

### Cache Miss Scenario

```mermaid
sequenceDiagram
    participant Browser
    participant Flask as Flask Server
    participant CM as cache_manager.py
    participant GC as gemini_client.py
    participant CacheFile as cache.json
    participant Gemini as Gemini API

    Browser->>Flask: POST /api/reasoning<br/>{lat, lon, co2, date...}
    activate Flask

    Flask->>Flask: Validate request parameters
    Flask->>CM: generate_cache_key(lat, lon, date)
    activate CM
    CM->>CM: SHA256(lat_lon_date)
    CM-->>Flask: cache_key
    deactivate CM

    Flask->>CM: get_cached_reasoning(cache_key)
    activate CM
    CM->>CacheFile: load_cache()
    activate CacheFile
    CacheFile-->>CM: JSON data
    deactivate CacheFile

    CM->>CM: Check if cache_key exists
    CM-->>Flask: None (cache miss)
    deactivate CM

    Flask->>GC: generate_inference(lat, lon, co2, ...)
    activate GC

    GC->>GC: generate_prompt(params)
    GC->>GC: load_api_key() from .env

    GC->>Gemini: POST https://generativelanguage.googleapis.com<br/>model.generate_content(prompt)
    activate Gemini

    Note over Gemini: Gemini processes request<br/>Generates reasoning (2-5s)

    Gemini-->>GC: Response {text: "reasoning..."}
    deactivate Gemini

    GC->>GC: Extract and validate response
    GC-->>Flask: reasoning (string)
    deactivate GC

    Flask->>CM: save_to_cache(cache_key, reasoning, metadata)
    activate CM
    CM->>CacheFile: load_cache()
    activate CacheFile
    CacheFile-->>CM: existing cache data
    deactivate CacheFile

    CM->>CM: Create cache entry<br/>{reasoning, cached_at, metadata}
    CM->>CacheFile: json.dump(updated_cache)
    activate CacheFile
    CacheFile-->>CM: Write complete
    deactivate CacheFile
    CM-->>Flask: True (success)
    deactivate CM

    Flask->>Flask: Build JSON response<br/>{reasoning, cached: false}
    Flask-->>Browser: 200 OK<br/>{reasoning, cached: false, cache_key}
    deactivate Flask

    Note over Browser,Gemini: Total time: ~2-6 seconds<br/>Includes Gemini API call + cache save
```

**Steps**:
1. Browser sends POST request with CO2 data
2. Flask validates required fields
3. cache_manager generates cache key
4. cache_manager checks cache.json
5. **Cache Miss**: Key not found
6. gemini_client generates prompt from parameters
7. gemini_client loads API key from .env
8. gemini_client calls Gemini API (2-5s)
9. Gemini returns reasoning text
10. cache_manager saves result to cache.json
11. Return response to browser (cached: false)

**Performance**:
- Latency: 2-6 seconds
- Bottleneck: Gemini API network call
- Cache saved for future requests

---

## Phase 2 - Data Flow (AWS)

### Cache Hit Scenario

```mermaid
sequenceDiagram
    participant Browser
    participant CF as CloudFront
    participant APIGW as API Gateway
    participant WAF
    participant Lambda
    participant DDB as DynamoDB
    participant CW as CloudWatch

    Browser->>CF: HTTPS POST /api/reasoning<br/>{lat, lon, co2, date...}
    activate CF
    CF->>APIGW: Forward request
    deactivate CF
    activate APIGW

    APIGW->>APIGW: Validate API Key
    APIGW->>APIGW: Check request schema
    APIGW->>WAF: Evaluate security rules
    activate WAF
    WAF->>WAF: Check rate limit (2000/5min)
    WAF->>WAF: Check IP reputation
    WAF-->>APIGW: Allow
    deactivate WAF

    APIGW->>Lambda: Invoke function<br/>Event: {body, headers, ...}
    activate Lambda

    Lambda->>Lambda: Parse JSON body
    Lambda->>Lambda: Validate parameters
    Lambda->>Lambda: generate_cache_key(lat, lon, date)
    Lambda->>Lambda: SHA256 hash

    Lambda->>DDB: GetItem<br/>Key: {cache_key: "abc123..."}
    activate DDB
    DDB->>DDB: Query partition key
    DDB-->>Lambda: Item found<br/>{cache_key, reasoning, cached_at, metadata, ttl}
    deactivate DDB

    Lambda->>Lambda: Check TTL not expired
    Lambda->>Lambda: Extract reasoning
    Lambda->>Lambda: Build response<br/>{reasoning, cached: true}

    Lambda->>CW: Log: Cache hit for key=abc123...

    Lambda-->>APIGW: Return {statusCode: 200, body: {...}}
    deactivate Lambda

    APIGW-->>CF: 200 OK + JSON body
    activate CF
    CF-->>Browser: 200 OK<br/>{reasoning, cached: true, cache_key}
    deactivate CF
    deactivate APIGW

    Note over Browser,DDB: Total time: ~100-200ms<br/>DynamoDB: <10ms, Lambda: 50-100ms
```

**Steps**:
1. Browser sends HTTPS POST to CloudFront
2. CloudFront forwards to API Gateway (no caching for POST)
3. API Gateway validates API key and request schema
4. WAF evaluates security rules (rate limit, IP checks)
5. Lambda function invoked with event
6. Lambda parses request and generates cache key
7. Lambda queries DynamoDB for cache_key
8. **Cache Hit**: Item found in DynamoDB
9. Lambda checks TTL not expired
10. Lambda extracts reasoning from item
11. Lambda logs to CloudWatch
12. Return response through stack (cached: true)

**Performance**:
- Total Latency: 100-200ms
- DynamoDB Query: <10ms (single-digit latency)
- Lambda Execution: 50-100ms (warm start)
- API Gateway: 20-30ms
- CloudFront: 20-50ms
- No external API calls

**Cost per Request**:
- Lambda: $0.0000002 (200ms @ 512MB)
- DynamoDB: $0.00000025 (1 RCU)
- API Gateway: $0.0000035 (per request)
- **Total**: ~$0.000004 per cache hit

---

### Cache Miss Scenario

```mermaid
sequenceDiagram
    participant Browser
    participant CF as CloudFront
    participant APIGW as API Gateway
    participant WAF
    participant Lambda
    participant DDB as DynamoDB
    participant SM as Secrets Manager
    participant Gemini as Gemini API
    participant CW as CloudWatch
    participant XRay as X-Ray

    Browser->>CF: HTTPS POST /api/reasoning<br/>{lat, lon, co2, date...}
    activate CF
    CF->>APIGW: Forward request
    deactivate CF
    activate APIGW

    APIGW->>APIGW: Validate API Key
    APIGW->>WAF: Evaluate security rules
    activate WAF
    WAF-->>APIGW: Allow
    deactivate WAF

    APIGW->>Lambda: Invoke function
    activate Lambda

    Lambda->>XRay: Start trace segment
    activate XRay

    Lambda->>Lambda: Parse and validate request
    Lambda->>Lambda: generate_cache_key()

    Lambda->>DDB: GetItem (cache_key)
    activate DDB
    DDB-->>Lambda: Item not found (cache miss)
    deactivate DDB

    Lambda->>XRay: Log: Cache miss

    Lambda->>SM: GetSecretValue<br/>SecretId: gemini-api-key
    activate SM
    SM->>SM: Decrypt secret with KMS
    SM-->>Lambda: {GEMINI_API_KEY: "AIza..."}
    deactivate SM

    Lambda->>Lambda: generate_prompt(params)
    Lambda->>Lambda: Configure genai.configure(api_key)

    Lambda->>Gemini: POST https://generativelanguage.googleapis.com<br/>model.generate_content(prompt)
    activate Gemini

    Note over Gemini: Gemini processes request<br/>Generates reasoning (2-5s)

    Gemini-->>Lambda: Response {text: "reasoning..."}
    deactivate Gemini

    Lambda->>Lambda: Validate response
    Lambda->>Lambda: Prepare DynamoDB item<br/>{cache_key, reasoning, metadata, ttl}
    Lambda->>Lambda: Calculate TTL (now + 90 days)

    Lambda->>DDB: PutItem<br/>{cache_key: "abc123", reasoning: "...", ttl: 1234567890}
    activate DDB
    DDB->>DDB: Write item (1 WCU)
    DDB-->>Lambda: Success
    deactivate DDB

    Lambda->>Lambda: Build response<br/>{reasoning, cached: false}

    Lambda->>CW: Log: Cache miss, API call successful
    Lambda->>XRay: End trace segment<br/>Duration: 3500ms
    deactivate XRay

    Lambda-->>APIGW: Return {statusCode: 200, body: {...}}
    deactivate Lambda

    APIGW-->>CF: 200 OK + JSON body
    activate CF
    CF-->>Browser: 200 OK<br/>{reasoning, cached: false, cache_key}
    deactivate CF
    deactivate APIGW

    Note over Browser,Gemini: Total time: ~3-6 seconds<br/>Dominated by Gemini API call (2-5s)
```

**Steps**:
1. Browser sends HTTPS POST to CloudFront
2. API Gateway validates API key, WAF checks rules
3. Lambda function invoked
4. X-Ray starts tracing
5. Lambda generates cache key
6. Lambda queries DynamoDB
7. **Cache Miss**: Item not found
8. Lambda retrieves API key from Secrets Manager
9. Secrets Manager decrypts with KMS
10. Lambda generates prompt
11. Lambda calls Gemini API (2-5s)
12. Gemini returns reasoning
13. Lambda calculates TTL (90 days from now)
14. Lambda saves result to DynamoDB with TTL
15. Lambda logs to CloudWatch
16. X-Ray records trace
17. Return response (cached: false)

**Performance**:
- Total Latency: 3-6 seconds
- DynamoDB Operations: <20ms (GetItem + PutItem)
- Secrets Manager: ~50-100ms (first call, then cached)
- Gemini API: 2-5 seconds (dominant factor)
- Lambda Execution: 3-6 seconds
- X-Ray Overhead: <10ms

**Cost per Request**:
- Lambda: $0.000003 (3s @ 512MB)
- DynamoDB: $0.00000150 (1 RCU + 1 WCU)
- API Gateway: $0.0000035
- Secrets Manager: $0.00000005 (cached after first call)
- **Total**: ~$0.000008 per cache miss

---

## Cache Key Generation

Both Phase 1 and Phase 2 use the same cache key algorithm:

```mermaid
flowchart LR
    Input["Input:<br/>lat=35.6762<br/>lon=139.6503<br/>date=2023-01-15"]
    Concat["Concatenate:<br/>'35.6762_139.6503_2023-01-15'"]
    Hash["SHA256 Hash"]
    Output["Cache Key:<br/>'a1b2c3d4e5f6...'<br/>(64 characters)"]

    Input --> Concat
    Concat --> Hash
    Hash --> Output

    style Input fill:#e3f2fd
    style Output fill:#c8e6c9
```

**Properties**:
- **Deterministic**: Same input always produces same key
- **Collision-resistant**: Different inputs produce different keys
- **Fixed length**: 64 characters (256 bits)
- **Consistent**: Works in both Phase 1 and Phase 2

**Example**:
```python
# Input
lat = 35.6762
lon = 139.6503
date = "2023-01-15"

# Concatenate
key_string = f"{lat}_{lon}_{date}"
# Result: "35.6762_139.6503_2023-01-15"

# Hash
cache_key = hashlib.sha256(key_string.encode('utf-8')).hexdigest()
# Result: "a1b2c3d4e5f6..." (64 hex characters)
```

---

## Cache TTL Flow (Phase 2 Only)

DynamoDB automatically deletes expired items based on the TTL attribute.

```mermaid
flowchart TB
    Write["Lambda writes item<br/>with TTL = now + 90 days"]
    Store["DynamoDB stores item<br/>{cache_key, reasoning, ttl}"]

    Time1["Time: Day 1-89<br/>Item is valid"]
    Access1["Lambda reads item<br/>TTL check: OK"]
    Return1["Return cached reasoning"]

    Time2["Time: Day 90<br/>TTL expires"]
    DDBProcess["DynamoDB background process<br/>scans for expired items"]
    Delete["Item marked for deletion<br/>(within 48 hours)"]

    Time3["Time: Day 91-92<br/>Item may still exist"]
    Access2["Lambda reads item<br/>TTL check: EXPIRED"]
    Miss["Treat as cache miss"]
    Rewrite["Call Gemini API<br/>Write new item with new TTL"]

    Write --> Store
    Store --> Time1
    Time1 --> Access1
    Access1 --> Return1

    Store --> Time2
    Time2 --> DDBProcess
    DDBProcess --> Delete

    Store --> Time3
    Time3 --> Access2
    Access2 --> Miss
    Miss --> Rewrite
    Rewrite --> Store

    style Write fill:#e3f2fd
    style Delete fill:#ffebee
    style Rewrite fill:#fff3e0
```

**TTL Behavior**:
1. Item written with `ttl = current_timestamp + (90 * 24 * 60 * 60)`
2. DynamoDB checks TTL in background (typically within 48 hours of expiration)
3. Expired items are automatically deleted (no cost)
4. Lambda should check TTL before using cached data
5. If item expired but not yet deleted, Lambda treats as cache miss

**Benefits**:
- Automatic cache invalidation
- No manual cleanup required
- No cost for deletions
- Keeps table size bounded

---

## Error Handling Flow

### Phase 1 Error Handling

```mermaid
flowchart TB
    Request["POST /api/reasoning"]

    ValidateReq["Validate Request"]
    ReqError{"Valid?"}
    Return400["Return 400<br/>{error: 'Missing fields'}"]

    CheckCache["Check Cache"]
    CacheHit{"Hit?"}
    ReturnCached["Return Cached<br/>200 OK"]

    CallAPI["Call Gemini API"]
    APIError{"Success?"}
    Return500["Return 500<br/>{error: 'API error'}"]

    SaveCache["Save to Cache"]
    SaveError{"Success?"}
    LogWarning["Log Warning<br/>(still return result)"]

    ReturnNew["Return New Result<br/>200 OK"]

    Request --> ValidateReq
    ValidateReq --> ReqError
    ReqError -->|No| Return400
    ReqError -->|Yes| CheckCache

    CheckCache --> CacheHit
    CacheHit -->|Yes| ReturnCached
    CacheHit -->|No| CallAPI

    CallAPI --> APIError
    APIError -->|No| Return500
    APIError -->|Yes| SaveCache

    SaveCache --> SaveError
    SaveError -->|No| LogWarning
    SaveError -->|Yes| ReturnNew
    LogWarning --> ReturnNew

    style Return400 fill:#ffebee
    style Return500 fill:#ffebee
    style LogWarning fill:#fff3e0
    style ReturnCached fill:#c8e6c9
    style ReturnNew fill:#c8e6c9
```

### Phase 2 Error Handling

```mermaid
flowchart TB
    Request["POST /api/reasoning"]

    WAFCheck["WAF Check"]
    WAFBlock{"Pass?"}
    Return403["Return 403<br/>WAF Block"]

    ValidateKey["Validate API Key"]
    KeyError{"Valid?"}
    Return401["Return 401<br/>Unauthorized"]

    ValidateReq["Validate Request"]
    ReqError{"Valid?"}
    Return400["Return 400<br/>Bad Request"]

    CheckCache["DynamoDB GetItem"]
    DBError1{"Success?"}
    LogError1["Log to CloudWatch"]

    CacheHit{"Hit?"}
    ReturnCached["Return 200<br/>Cached Result"]

    GetSecret["Get Secret"]
    SecretError{"Success?"}
    Return500a["Return 500<br/>Secret error"]

    CallAPI["Call Gemini API"]
    APIError{"Success?"}
    Retry["Retry Once"]
    RetryError{"Success?"}
    Return500b["Return 500<br/>API error"]

    SaveCache["DynamoDB PutItem"]
    DBError2{"Success?"}
    LogError2["Log Warning"]

    ReturnNew["Return 200<br/>New Result"]

    TriggerAlarm["CloudWatch Alarm<br/>Error Rate > 5%"]
    SendSNS["SNS Notification<br/>Email Alert"]

    Request --> WAFCheck
    WAFCheck --> WAFBlock
    WAFBlock -->|No| Return403
    WAFBlock -->|Yes| ValidateKey

    ValidateKey --> KeyError
    KeyError -->|No| Return401
    KeyError -->|Yes| ValidateReq

    ValidateReq --> ReqError
    ReqError -->|No| Return400
    ReqError -->|Yes| CheckCache

    CheckCache --> DBError1
    DBError1 -->|No| LogError1
    LogError1 --> Return500a
    DBError1 -->|Yes| CacheHit

    CacheHit -->|Yes| ReturnCached
    CacheHit -->|No| GetSecret

    GetSecret --> SecretError
    SecretError -->|No| Return500a
    SecretError -->|Yes| CallAPI

    CallAPI --> APIError
    APIError -->|No| Retry
    Retry --> RetryError
    RetryError -->|No| Return500b
    RetryError -->|Yes| SaveCache
    APIError -->|Yes| SaveCache

    SaveCache --> DBError2
    DBError2 -->|No| LogError2
    DBError2 -->|Yes| ReturnNew
    LogError2 --> ReturnNew

    Return500a --> TriggerAlarm
    Return500b --> TriggerAlarm
    TriggerAlarm --> SendSNS

    style Return403 fill:#ffebee
    style Return401 fill:#ffebee
    style Return400 fill:#ffebee
    style Return500a fill:#ffebee
    style Return500b fill:#ffebee
    style LogError1 fill:#fff3e0
    style LogError2 fill:#fff3e0
    style ReturnCached fill:#c8e6c9
    style ReturnNew fill:#c8e6c9
```

---

## Performance Comparison

### Cache Hit Performance

| Metric | Phase 1 (Local) | Phase 2 (AWS) |
|--------|-----------------|---------------|
| Total Latency | 50-100ms | 100-200ms |
| Cache Lookup | 20-50ms (file I/O) | <10ms (DynamoDB) |
| Response Build | 10-20ms | 50-100ms (Lambda) |
| Network Overhead | Minimal (localhost) | 50-100ms (CloudFront + API Gateway) |
| Cost per Request | $0 | ~$0.000004 |

### Cache Miss Performance

| Metric | Phase 1 (Local) | Phase 2 (AWS) |
|--------|-----------------|---------------|
| Total Latency | 2-6s | 3-6s |
| Cache Lookup | 20-50ms | <10ms |
| API Call | 2-5s | 2-5s |
| Cache Save | 50-100ms (file write) | <10ms (DynamoDB) |
| Secret Retrieval | N/A (.env file) | 50-100ms (first call) |
| Cost per Request | $0 (plus API quota) | ~$0.000008 |

### Throughput

| Metric | Phase 1 | Phase 2 |
|--------|---------|---------|
| Max Concurrent | ~10-20 (Flask dev server) | 1000+ (Lambda) |
| Requests/sec (cached) | ~10-20 | 100+ (with provisioned concurrency) |
| Requests/sec (uncached) | ~0.2-0.5 (API bottleneck) | Same (Gemini API limited) |

---

## Summary

### Key Differences

1. **Cache Storage**:
   - Phase 1: Local JSON file (cache.json)
   - Phase 2: DynamoDB with TTL

2. **Performance**:
   - Phase 1: Faster for cache hits (no network), limited concurrency
   - Phase 2: Slightly slower per request, massively scalable

3. **Cost**:
   - Phase 1: Free (local), but requires running server
   - Phase 2: Pay-per-use (~$0.000004-0.000008 per request)

4. **Reliability**:
   - Phase 1: Single point of failure, no redundancy
   - Phase 2: Multi-AZ, automatic failover, backups

5. **Monitoring**:
   - Phase 1: Manual log checking
   - Phase 2: CloudWatch, X-Ray, automated alarms

The data flow diagrams show that while Phase 2 has more components, the overall flow logic remains similar, making migration straightforward.
