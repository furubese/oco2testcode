# Component Interaction Diagrams

## Overview

This document details how components interact with each other in both Phase 1 and Phase 2, showing the relationships, dependencies, and communication patterns.

---

## Phase 1 - Component Interaction

### High-Level Component Diagram

```mermaid
graph TB
    subgraph "Frontend Components"
        HTML["sample_calendar.html<br/>• Leaflet Map<br/>• Date Selector<br/>• Sidepanel UI"]
    end

    subgraph "Flask Application (app.py)"
        Routes["Route Handlers<br/>• index()<br/>• serve_static()<br/>• health_check()<br/>• reasoning()"]
        ErrorHandlers["Error Handlers<br/>• method_not_allowed()<br/>• Exception handlers"]
    end

    subgraph "Business Logic Layer"
        CM["CacheManager<br/>(cache_manager.py)<br/>• generate_cache_key()<br/>• load_cache()<br/>• get_cached_reasoning()<br/>• save_to_cache()"]

        GC["GeminiClient<br/>(gemini_client.py)<br/>• load_api_key()<br/>• generate_prompt()<br/>• call_gemini_api()<br/>• generate_inference()"]
    end

    subgraph "Data Layer"
        CacheFile["cache.json<br/>Key-Value Store"]
        EnvFile[".env<br/>Configuration"]
        GeoJSON["*.geojson<br/>CO2 Data Files"]
    end

    subgraph "External Services"
        Gemini["Gemini API<br/>google.generativeai"]
    end

    HTML -->|"HTTP GET /"| Routes
    HTML -->|"HTTP GET *.geojson"| Routes
    HTML -->|"HTTP POST /api/reasoning"| Routes

    Routes -->|"delegate"| CM
    Routes -->|"delegate"| GC
    Routes -->|"handle errors"| ErrorHandlers

    CM <-->|"read/write"| CacheFile
    GC -->|"read"| EnvFile
    GC -->|"API call"| Gemini

    Routes -->|"serve"| GeoJSON

    style HTML fill:#e3f2fd
    style Routes fill:#fff3e0
    style CM fill:#f3e5f5
    style GC fill:#f3e5f5
    style CacheFile fill:#ffebee
    style Gemini fill:#e8f5e9
```

### Detailed Interaction: API Request Processing

```mermaid
graph LR
    subgraph "Request Flow"
        direction TB
        Request["HTTP Request"] --> CORS["CORS Middleware"]
        CORS --> RouteDispatch["Route Dispatcher"]
        RouteDispatch --> RouteHandler["Route Handler<br/>/api/reasoning"]
    end

    subgraph "Business Logic"
        direction TB
        RouteHandler --> Validate["Parameter Validation"]
        Validate --> CacheCheck["Cache Manager<br/>Check Cache"]
        CacheCheck -->|"Hit"| BuildResponse["Build Response"]
        CacheCheck -->|"Miss"| GeminiCall["Gemini Client<br/>API Call"]
        GeminiCall --> CacheSave["Cache Manager<br/>Save Result"]
        CacheSave --> BuildResponse
    end

    subgraph "Response Flow"
        direction TB
        BuildResponse --> JSONify["JSON Serialization"]
        JSONify --> HTTPResponse["HTTP Response"]
    end

    style Request fill:#e3f2fd
    style CacheCheck fill:#f3e5f5
    style GeminiCall fill:#f3e5f5
    style HTTPResponse fill:#c8e6c9
```

### Module Dependencies

```mermaid
graph TB
    app["app.py<br/>(Flask Application)"]
    cm["cache_manager.py<br/>(Cache Operations)"]
    gc["gemini_client.py<br/>(AI Client)"]

    flask["flask<br/>(Web Framework)"]
    cors["flask_cors<br/>(CORS Support)"]
    genai["google.generativeai<br/>(Gemini SDK)"]
    json["json<br/>(Serialization)"]
    hashlib["hashlib<br/>(Hashing)"]
    os["os<br/>(File System)"]
    dotenv["python-dotenv<br/>(Config)"]

    app --> flask
    app --> cors
    app --> cm
    app --> gc
    app --> dotenv

    cm --> json
    cm --> hashlib
    cm --> os

    gc --> genai
    gc --> os

    style app fill:#fff3e0
    style cm fill:#f3e5f5
    style gc fill:#f3e5f5
    style flask fill:#e1f5ff
    style genai fill:#e8f5e9
```

### Communication Patterns

#### Pattern 1: Synchronous Request-Response
```
Browser → Flask → CacheManager → Local File → Response
         ↓
         → GeminiClient → External API → Response
```

#### Pattern 2: Error Propagation
```
GeminiClient (Exception) → Flask (Catch) → Browser (Error Response)
```

#### Pattern 3: Cache-Aside Pattern
```
1. Check cache (cache_manager.get_cached_reasoning)
2. If miss: Fetch from source (gemini_client.generate_inference)
3. Save to cache (cache_manager.save_to_cache)
4. Return result
```

---

## Phase 2 - Component Interaction

### High-Level Component Diagram

```mermaid
graph TB
    subgraph "Frontend Layer"
        Browser["Browser<br/>sample_calendar.html<br/>Leaflet Map"]
    end

    subgraph "Edge Layer"
        CloudFront["CloudFront<br/>• Edge Caching<br/>• SSL Termination<br/>• Origin Routing"]
    end

    subgraph "API Layer"
        APIGW["API Gateway<br/>• Endpoint: /api/reasoning<br/>• API Key Auth<br/>• Request Validation"]

        WAF["WAF<br/>• Rate Limiting<br/>• Security Rules"]
    end

    subgraph "Compute Layer"
        Lambda["Lambda Function<br/>reasoning_handler<br/>• Python 3.11<br/>• 512MB Memory"]

        LambdaLayer["Lambda Layer<br/>• google-generativeai<br/>• boto3"]
    end

    subgraph "Data & Config Layer"
        DynamoDB["DynamoDB<br/>CO2ReasoningCache<br/>• PK: cache_key<br/>• TTL: 90 days"]

        S3Static["S3 Static<br/>• HTML/JS/CSS<br/>• Config Files"]

        S3Data["S3 Data<br/>• GeoJSON Files"]

        SecretsManager["Secrets Manager<br/>• GEMINI_API_KEY"]

        SSM["Parameter Store<br/>• App Config"]
    end

    subgraph "Monitoring Layer"
        CloudWatch["CloudWatch<br/>• Logs<br/>• Metrics<br/>• Alarms"]

        XRay["X-Ray<br/>• Distributed Tracing"]

        SNS["SNS<br/>• Alerts"]
    end

    subgraph "Security Layer"
        IAM["IAM<br/>• Roles<br/>• Policies"]
    end

    subgraph "External Services"
        Gemini["Gemini API"]
    end

    Browser -->|"HTTPS"| CloudFront
    CloudFront -->|"static"| S3Static
    CloudFront -->|"data"| S3Data
    CloudFront -->|"API"| APIGW

    APIGW --> WAF
    WAF --> Lambda
    Lambda --> LambdaLayer

    Lambda -->|"GetItem/PutItem"| DynamoDB
    Lambda -->|"GetSecretValue"| SecretsManager
    Lambda -->|"GetParameter"| SSM
    Lambda -->|"API Call"| Gemini

    Lambda -->|"Logs"| CloudWatch
    Lambda -->|"Traces"| XRay
    CloudWatch -->|"Trigger"| SNS

    IAM -.->|"Authorize"| Lambda
    IAM -.->|"Authorize"| DynamoDB
    IAM -.->|"Authorize"| SecretsManager

    style Browser fill:#e3f2fd
    style CloudFront fill:#ff9800
    style APIGW fill:#2196f3
    style Lambda fill:#9c27b0
    style DynamoDB fill:#ff5722
    style Gemini fill:#e8f5e9
```

### Detailed Interaction: Lambda Function Internal

```mermaid
graph TB
    subgraph "Lambda Handler"
        Entry["lambda_handler()<br/>Entry Point"]

        ParseEvent["Parse Event<br/>• Extract body<br/>• Parse JSON<br/>• Extract headers"]

        Validate["Validate Request<br/>• Required fields<br/>• Data types<br/>• Value ranges"]

        GenKey["Generate Cache Key<br/>SHA256(lat_lon_date)"]
    end

    subgraph "Cache Layer"
        CheckCache["Check DynamoDB<br/>GetItem(cache_key)"]

        CacheHit{"Cache Hit?"}

        SaveCache["Save to DynamoDB<br/>PutItem(cache_key, reasoning, ttl)"]
    end

    subgraph "AI Integration"
        GetSecret["Get API Key<br/>Secrets Manager"]

        BuildPrompt["Build Prompt<br/>Format CO2 data"]

        CallGemini["Call Gemini API<br/>generate_content()"]

        ParseResponse["Parse Response<br/>Extract reasoning"]
    end

    subgraph "Response Building"
        BuildResp["Build Response<br/>statusCode: 200<br/>body: JSON"]

        Return["Return Response"]
    end

    subgraph "Error Handling"
        CatchError["Exception Handler"]
        LogError["Log to CloudWatch"]
        BuildError["Build Error Response<br/>statusCode: 500"]
    end

    Entry --> ParseEvent
    ParseEvent --> Validate
    Validate --> GenKey
    GenKey --> CheckCache

    CheckCache --> CacheHit
    CacheHit -->|"Yes"| BuildResp
    CacheHit -->|"No"| GetSecret

    GetSecret --> BuildPrompt
    BuildPrompt --> CallGemini
    CallGemini --> ParseResponse
    ParseResponse --> SaveCache
    SaveCache --> BuildResp

    BuildResp --> Return

    ParseEvent -.->|"Error"| CatchError
    Validate -.->|"Error"| CatchError
    GetSecret -.->|"Error"| CatchError
    CallGemini -.->|"Error"| CatchError

    CatchError --> LogError
    LogError --> BuildError
    BuildError --> Return

    style Entry fill:#fff3e0
    style CacheHit fill:#f3e5f5
    style CallGemini fill:#e8f5e9
    style Return fill:#c8e6c9
    style CatchError fill:#ffebee
```

### AWS Service Interactions

```mermaid
sequenceDiagram
    participant Lambda
    participant IAM
    participant DDB as DynamoDB
    participant SM as Secrets Manager
    participant SSM
    participant CW as CloudWatch
    participant XRay

    Note over Lambda: Lambda Execution Starts

    Lambda->>IAM: Assume execution role
    IAM-->>Lambda: Temporary credentials

    Lambda->>XRay: Start trace segment
    activate XRay

    Lambda->>DDB: GetItem request
    activate DDB
    IAM->>DDB: Authorize (check IAM policy)
    DDB-->>Lambda: Item response
    deactivate DDB

    alt Cache Miss
        Lambda->>SM: GetSecretValue
        activate SM
        IAM->>SM: Authorize
        SM->>SM: Decrypt with KMS
        SM-->>Lambda: Secret value
        deactivate SM

        Lambda->>SSM: GetParameter
        activate SSM
        IAM->>SSM: Authorize
        SSM-->>Lambda: Parameter value
        deactivate SSM

        Note over Lambda: Call Gemini API

        Lambda->>DDB: PutItem request
        activate DDB
        IAM->>DDB: Authorize
        DDB-->>Lambda: Success
        deactivate DDB
    end

    Lambda->>CW: Write logs
    Lambda->>CW: Put custom metrics
    Lambda->>XRay: End trace segment
    deactivate XRay

    Note over Lambda: Lambda Execution Ends
```

### CDK Component Relationships

```mermaid
graph TB
    subgraph "CDK Constructs"
        BaseConstruct["BaseStack Construct<br/>• IAM Role<br/>• Secrets<br/>• Parameters"]

        StorageConstruct["StorageStack Construct<br/>• DynamoDB Table<br/>• S3 Buckets"]

        LambdaConstruct["LambdaStack Construct<br/>• Lambda Function<br/>• Lambda Layer"]

        ApiConstruct["ApiStack Construct<br/>• API Gateway<br/>• WAF"]

        FrontendConstruct["FrontendStack Construct<br/>• S3 Static<br/>• CloudFront<br/>• OAI"]

        MonitoringConstruct["ObservabilityStack Construct<br/>• CloudWatch<br/>• Alarms<br/>• SNS"]
    end

    subgraph "CDK Dependencies"
        BaseConstruct -->|"exports"| LambdaConstruct
        StorageConstruct -->|"exports"| LambdaConstruct
        LambdaConstruct -->|"exports"| ApiConstruct
        ApiConstruct -->|"exports"| FrontendConstruct
        StorageConstruct -->|"exports"| FrontendConstruct

        LambdaConstruct -->|"exports"| MonitoringConstruct
        ApiConstruct -->|"exports"| MonitoringConstruct
        FrontendConstruct -->|"exports"| MonitoringConstruct
    end

    subgraph "CloudFormation Exports"
        Exports["CloudFormation Stack Exports<br/>• lambdaRoleArn<br/>• dynamodbTableName<br/>• apiEndpoint<br/>• cloudfrontUrl<br/>• etc."]
    end

    BaseConstruct -.->|"CfnOutput"| Exports
    StorageConstruct -.->|"CfnOutput"| Exports
    LambdaConstruct -.->|"CfnOutput"| Exports
    ApiConstruct -.->|"CfnOutput"| Exports
    FrontendConstruct -.->|"CfnOutput"| Exports

    style BaseConstruct fill:#795548
    style StorageConstruct fill:#4caf50
    style LambdaConstruct fill:#9c27b0
    style ApiConstruct fill:#2196f3
    style FrontendConstruct fill:#ff9800
    style MonitoringConstruct fill:#00bcd4
```

### Communication Patterns

#### Pattern 1: Request-Response with Caching
```
Browser → CloudFront → API Gateway → Lambda → DynamoDB (check)
                                             ↓ (miss)
                                             Secrets Manager → Gemini API
                                             ↓
                                             DynamoDB (save) → Response
```

#### Pattern 2: Asynchronous Monitoring
```
Lambda → CloudWatch Logs (async)
       → X-Ray (async)
       → CloudWatch Metrics (async)

CloudWatch Alarms → SNS → Email (when threshold exceeded)
```

#### Pattern 3: IAM Authorization
```
Every AWS service call:
1. Lambda uses execution role
2. IAM evaluates policy
3. Allow or Deny
4. Service executes (if allowed)
```

#### Pattern 4: Secret Management
```
Lambda cold start:
1. GetSecretValue (Secrets Manager)
2. Decrypt with KMS
3. Cache in memory
4. Reuse for warm invocations
```

---

## Component Communication Matrix

### Phase 1 Communication Matrix

| Component | Communicates With | Protocol | Direction | Purpose |
|-----------|------------------|----------|-----------|---------|
| Browser | Flask | HTTP | Bidirectional | API requests |
| Flask | cache_manager | Function Call | Unidirectional | Cache operations |
| Flask | gemini_client | Function Call | Unidirectional | AI inference |
| cache_manager | cache.json | File I/O | Bidirectional | Data persistence |
| gemini_client | Gemini API | HTTPS | Unidirectional | AI generation |
| gemini_client | .env | File I/O | Read-only | Configuration |

### Phase 2 Communication Matrix

| Component | Communicates With | Protocol | Direction | Purpose |
|-----------|------------------|----------|-----------|---------|
| Browser | CloudFront | HTTPS | Bidirectional | Content delivery |
| CloudFront | API Gateway | HTTPS | Bidirectional | API proxy |
| CloudFront | S3 | HTTPS | Read-only | Static content |
| API Gateway | Lambda | Event-driven | Unidirectional | Function invocation |
| API Gateway | WAF | Integration | Bidirectional | Security filtering |
| Lambda | DynamoDB | AWS API | Bidirectional | Data operations |
| Lambda | Secrets Manager | AWS API | Read-only | Secret retrieval |
| Lambda | SSM | AWS API | Read-only | Config retrieval |
| Lambda | Gemini API | HTTPS | Unidirectional | AI generation |
| Lambda | CloudWatch | AWS API | Write-only | Logging/metrics |
| Lambda | X-Ray | AWS API | Write-only | Tracing |
| CloudWatch | SNS | Event-driven | Unidirectional | Alarm notifications |
| IAM | All AWS Services | Authorization | Bidirectional | Access control |

---

## Integration Points

### Phase 1 → Phase 2 Migration Mapping

| Phase 1 Component | Phase 2 Component(s) | Changes Required |
|------------------|---------------------|------------------|
| Flask routes | API Gateway + Lambda | Convert to Lambda handlers |
| cache_manager.py | Lambda + DynamoDB SDK | Replace file I/O with DynamoDB calls |
| gemini_client.py | Lambda (same logic) | Add Secrets Manager integration |
| cache.json | DynamoDB Table | Migrate data, add TTL |
| .env file | Secrets Manager + SSM | Store secrets securely |
| Static files | S3 + CloudFront | Upload files, configure CDN |
| Local logs | CloudWatch Logs | Automatic (Lambda integration) |

### Key Integration Challenges

1. **State Management**:
   - Phase 1: File-based (cache.json)
   - Phase 2: DynamoDB (requires schema design)

2. **Authentication**:
   - Phase 1: None
   - Phase 2: API Key + IAM (requires key management)

3. **Error Handling**:
   - Phase 1: Flask exception handlers
   - Phase 2: Lambda + CloudWatch Alarms (requires monitoring setup)

4. **Secrets**:
   - Phase 1: .env file
   - Phase 2: Secrets Manager (requires secure migration)

5. **Deployment**:
   - Phase 1: Manual (python app.py)
   - Phase 2: CDK (requires IaC knowledge)

---

## Component Lifecycle

### Phase 1 Lifecycle

```
1. Start: python app.py
2. Load: Import modules, read .env
3. Run: Flask server listens on port 5000
4. Request: Handle HTTP requests synchronously
5. Stop: Ctrl+C (graceful shutdown)
```

### Phase 2 Lifecycle

#### Lambda Function Lifecycle
```
1. Cold Start (first invocation or after idle):
   - Download code package
   - Initialize runtime (Python 3.11)
   - Load Lambda layer
   - Import modules
   - Execute init code
   - Cache secrets
   Duration: 1-3 seconds

2. Warm Invocation (subsequent calls):
   - Reuse existing container
   - Execute handler function
   - Reuse cached secrets/connections
   Duration: 50-200ms

3. Idle Timeout (15 minutes):
   - Container frozen
   - Next invocation = cold start
```

#### CDK Stack Lifecycle
```
1. Synth: cdk synth (generate CloudFormation)
2. Deploy: cdk deploy (create/update resources)
3. Update: cdk deploy (modify existing resources)
4. Rollback: Automatic on failure
5. Destroy: cdk destroy (delete all resources)
```

---

## Summary

### Phase 1 Strengths
- **Simple**: Few components, easy to understand
- **Fast Development**: Quick iteration, no deploy cycle
- **Cheap**: No cloud costs

### Phase 1 Weaknesses
- **Not Scalable**: Single-threaded Flask
- **No Redundancy**: Single point of failure
- **Limited Monitoring**: Manual log checking

### Phase 2 Strengths
- **Scalable**: Auto-scaling Lambda and DynamoDB
- **Reliable**: Multi-AZ, automatic failover
- **Monitored**: CloudWatch, X-Ray, automated alerts
- **Secure**: IAM, WAF, Secrets Manager

### Phase 2 Weaknesses
- **Complex**: Many components, steep learning curve
- **Cost**: Pay-per-use (though minimal)
- **Cold Starts**: Lambda cold start latency

The component interaction diagrams show that while Phase 2 has more moving parts, the core business logic remains the same, making the migration primarily an infrastructure change rather than a logic rewrite.
