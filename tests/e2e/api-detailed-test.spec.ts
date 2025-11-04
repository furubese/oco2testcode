import { test, expect } from '@playwright/test';

const API_GATEWAY_URL = 'https://of1svnz3yk.execute-api.us-east-1.amazonaws.com/prod';

test.describe('API Detailed Diagnostics', () => {

  test('should test API with multiple request variations', async ({ page }) => {
    // Test 1: Correct format
    console.log('\n=== Test 1: Correct Frontend Format ===');
    const correctData = {
      lat: 35.6812,
      lon: 139.7671,
      co2: 420.5,
      deviation: 8.2,
      date: '2023-05-15',
      severity: 'high',
      zscore: 3.5
    };

    let response = await page.request.post(`${API_GATEWAY_URL}/reasoning`, {
      headers: { 'Content-Type': 'application/json' },
      data: correctData,
    });

    console.log('Status:', response.status());
    const body1 = await response.text();
    console.log('Response:', body1);

    // Test 2: With unknown severity (from frontend code line 567)
    console.log('\n=== Test 2: With "unknown" severity ===');
    const unknownSeverityData = {
      lat: 35.6812,
      lon: 139.7671,
      co2: 420.5,
      deviation: 8.2,
      date: 'unknown',  // Frontend may send 'unknown' if detection_files is empty
      severity: 'unknown',  // Frontend sends 'unknown' if severity is missing
      zscore: 3.5
    };

    response = await page.request.post(`${API_GATEWAY_URL}/reasoning`, {
      headers: { 'Content-Type': 'application/json' },
      data: unknownSeverityData,
    });

    console.log('Status:', response.status());
    const body2 = await response.text();
    console.log('Response:', body2);

    // Test 3: Test CORS preflight
    console.log('\n=== Test 3: CORS OPTIONS Request ===');
    const optionsResponse = await page.request.fetch(`${API_GATEWAY_URL}/reasoning`, {
      method: 'OPTIONS',
      headers: {
        'Origin': 'https://dy0dc92sru60q.cloudfront.net',
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'content-type'
      }
    });

    console.log('CORS Status:', optionsResponse.status());
    console.log('CORS Headers:', optionsResponse.headers());
  });

  test('should check CDK stack outputs and config', async ({ page }) => {
    console.log('\n=== Checking API Gateway Configuration ===');

    // Try to check if the API endpoint is responding at all
    try {
      const healthResponse = await page.request.get(API_GATEWAY_URL);
      console.log('API Gateway root status:', healthResponse.status());
    } catch (e) {
      console.log('API Gateway root not accessible:', (e as Error).message);
    }

    // Check if /reasoning endpoint exists
    try {
      const getResponse = await page.request.get(`${API_GATEWAY_URL}/reasoning`);
      console.log('GET /reasoning status:', getResponse.status());
      console.log('GET /reasoning body:', await getResponse.text());
    } catch (e) {
      console.log('GET /reasoning error:', (e as Error).message);
    }
  });
});
