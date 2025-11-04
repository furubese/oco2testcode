import { test } from '@playwright/test';

const API_GATEWAY_URL = 'https://of1svnz3yk.execute-api.us-east-1.amazonaws.com/prod';

test('Debug API validation errors', async ({ page }) => {
  console.log('\n=== Test 1: All required fields with valid values ===');
  const validData = {
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
    data: validData,
  });

  console.log('Status:', response.status());
  const body1 = await response.text();
  console.log('Response:', body1);

  console.log('\n=== Test 2: Minimal required fields only (lat, lon, co2) ===');
  const minimalData = {
    lat: 35.6812,
    lon: 139.7671,
    co2: 420.5
  };

  response = await page.request.post(`${API_GATEWAY_URL}/reasoning`, {
    headers: { 'Content-Type': 'application/json' },
    data: minimalData,
  });

  console.log('Status:', response.status());
  const body2 = await response.text();
  console.log('Response:', body2);

  console.log('\n=== Test 3: With unknown severity ===');
  const unknownSeverityData = {
    lat: 35.6812,
    lon: 139.7671,
    co2: 420.5,
    deviation: 8.2,
    date: '2023-05-15',
    severity: 'unknown',
    zscore: 3.5
  };

  response = await page.request.post(`${API_GATEWAY_URL}/reasoning`, {
    headers: { 'Content-Type': 'application/json' },
    data: unknownSeverityData,
  });

  console.log('Status:', response.status());
  const body3 = await response.text();
  console.log('Response:', body3);

  console.log('\n=== Test 4: With unknown date AND severity ===');
  const unknownBothData = {
    lat: 35.6812,
    lon: 139.7671,
    co2: 420.5,
    deviation: 8.2,
    date: 'unknown',
    severity: 'unknown',
    zscore: 3.5
  };

  response = await page.request.post(`${API_GATEWAY_URL}/reasoning`, {
    headers: { 'Content-Type': 'application/json' },
    data: unknownBothData,
  });

  console.log('Status:', response.status());
  const body4 = await response.text();
  console.log('Response:', body4);
});
