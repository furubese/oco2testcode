# Fix: API Gateway URL configuration in config.js

## Problem
CloudFront deployed `config.js` with `API_GATEWAY_URL` hardcoded to `http://localhost:5000`, causing reasoning API calls to fail with network errors.

When users click on map markers, they see:
```
⚠️ ネットワークエラー
サーバーに接続できませんでした。Flaskサーバーが起動しているか確認してください。
💡 別のマーカーをクリックして再度お試しください。
```

## Root Cause Analysis
Playwright E2E tests identified the issue:
- ❌ `config.js` template had hardcoded localhost URL instead of placeholder
- ❌ `frontend-stack.ts` was not replacing the API_GATEWAY_URL placeholder
- ❌ `co2-analysis-app.ts` was not passing apiGatewayUrl to FrontendStack

### Test Results (Before Fix)
```bash
npm run test:chromium -- tests/e2e/cloudfront-api-config.spec.ts

Current API Configuration: {
  API_GATEWAY_URL: 'http://localhost:5000',  ❌ Problem!
  CLOUDFRONT_URL: 'https://dy0dc92sru60q.cloudfront.net',
  ENDPOINTS: { REASONING: '/reasoning' }
}

❌ 1 failed - API Gateway URL configuration test
✅ 7 passed - Other configuration tests
```

## Solution

### 1. Updated config.js template
```javascript
// Before
API_GATEWAY_URL: 'http://localhost:5000', // Default to local development

// After
API_GATEWAY_URL: '{{API_GATEWAY_URL}}', // Will be replaced during CDK deployment
ENVIRONMENT: '{{ENVIRONMENT}}',          // Will be replaced during CDK deployment
```

### 2. Updated frontend-stack.ts
- Added `apiGatewayUrl: string` to `FrontendStackProps` interface
- Added placeholder replacement in config.js generation:
  ```typescript
  configContent = configContent
    .replace(/\{\{API_GATEWAY_URL\}\}/g, props.apiGatewayUrl)
    .replace(/\{\{CLOUDFRONT_URL\}\}/g, this.cloudFrontUrl)
    .replace(/\{\{GEOJSON_BASE_URL\}\}/g, `${this.cloudFrontUrl}/data/geojson`)
    .replace(/\{\{ENVIRONMENT\}\}/g, config.environment);
  ```

### 3. Updated co2-analysis-app.ts
```typescript
const frontendStack = new FrontendStack(app, 'FrontendStack', config, {
  env,
  staticWebsiteBucket: storageStack.staticWebsiteBucket,
  geoJsonBucket: storageStack.geoJsonBucket,
  originAccessIdentity: storageStack.originAccessIdentity,
  apiGatewayUrl: computeStack.api.url, // ✅ Pass API Gateway URL from ComputeStack
  tags: { Layer: '5-Frontend' },
});
```

## Files Changed
- `config.js` - Template with placeholders
- `cdk/lib/frontend-stack.ts` - Config generation logic
- `cdk/bin/co2-analysis-app.ts` - Stack wiring

## Testing

### Playwright E2E Tests
Added comprehensive configuration tests:
```bash
npm run test:chromium -- tests/e2e/cloudfront-api-config.spec.ts
```

**Test Coverage**:
- ✅ API Gateway URL is correctly configured (not localhost)
- ✅ config.js loads successfully
- ✅ APP_CONFIG is available globally
- ✅ Reasoning endpoint is configured
- ✅ No CORS errors
- ✅ Config.js content verification

**Expected After Fix**: ✅ 8/8 tests pass

### Manual Testing
1. Deploy CDK stacks
2. Visit CloudFront URL: https://dy0dc92sru60q.cloudfront.net/
3. Open browser DevTools console
4. Verify configuration:
   ```javascript
   console.log(window.APP_CONFIG.API_GATEWAY_URL);
   // Expected: "https://{api-id}.execute-api.us-east-1.amazonaws.com/prod"
   ```
5. Click on map marker
6. Verify reasoning results appear (no network error)

## Impact

### Before Fix
- ❌ Frontend tries to connect to `http://localhost:5000`
- ❌ Network connection fails
- ❌ Users see "ネットワークエラー" error
- ❌ **Reasoning feature completely broken**

### After Fix
- ✅ Frontend connects to correct API Gateway URL
- ✅ API calls succeed
- ✅ Reasoning results display correctly
- ✅ **Main feature works as expected**

## Deployment Instructions

After merging this PR:

```bash
# Navigate to CDK directory
cd cdk

# Deploy all stacks (dev environment)
cdk deploy --all --context environment=dev --profile fse

# Verify deployment
# Check CloudFront URL
curl https://dy0dc92sru60q.cloudfront.net/config.js | grep API_GATEWAY_URL

# Expected output:
# API_GATEWAY_URL: 'https://{api-id}.execute-api.us-east-1.amazonaws.com/prod',
```

### Verification Checklist
- [ ] CDK deployment completes successfully
- [ ] config.js contains production API Gateway URL (not localhost)
- [ ] CloudFront cache invalidated for `/config.js`
- [ ] Frontend loads without errors
- [ ] Map markers clickable
- [ ] Reasoning results display correctly
- [ ] Playwright tests pass

## Related Files Created

### Documentation
- `API_CONFIGURATION_ISSUE.md` - Detailed problem analysis
- `REASONING_ISSUE_SUMMARY.md` - Quick reference guide
- `CLOUDFRONT_TEST_RESULTS.md` - E2E test results

### Tests
- `tests/e2e/cloudfront-api-config.spec.ts` - Configuration validation tests
- `tests/e2e/cloudfront-co2-map.spec.ts` - Functional tests

## References
- Issue: Reasoning feature not working
- CloudFront URL: https://dy0dc92sru60q.cloudfront.net/
- Detection Method: Playwright E2E Tests
- Test Framework: Playwright 1.56.1

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
