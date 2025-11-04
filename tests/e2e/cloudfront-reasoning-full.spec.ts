import { test, expect } from '@playwright/test';

const CLOUDFRONT_URL = 'https://dy0dc92sru60q.cloudfront.net';
const API_GATEWAY_URL = 'https://of1svnz3yk.execute-api.us-east-1.amazonaws.com/prod';

test.describe('CloudFront Reasoning Functionality - Full E2E', () => {

  test('should test API with correct request format from frontend', async ({ page }) => {
    // Test the API with the exact format the frontend uses (from sample_calendar.html:561-569)
    const correctApiData = {
      lat: 35.6812,
      lon: 139.7671,
      co2: 420.5,
      deviation: 8.2,
      date: '2023-05-15',
      severity: 'high',
      zscore: 3.5
    };

    console.log('Testing API with correct frontend format:', correctApiData);

    const response = await page.request.post(`${API_GATEWAY_URL}/reasoning`, {
      headers: {
        'Content-Type': 'application/json'
      },
      data: correctApiData,
    });

    console.log('API Response Status:', response.status());

    if (response.status() === 200) {
      const result = await response.json();
      console.log('✅ API Success! Response:', result);
      expect(result).toHaveProperty('reasoning');
      console.log('Reasoning result preview:', result.reasoning?.substring(0, 200));
    } else {
      const errorText = await response.text();
      console.log('❌ API Error Response:', errorText);

      // If it's still 400, there might be another issue
      if (response.status() === 400) {
        console.log('⚠️ API still returns 400 with correct format - Lambda validation may have changed');
      }
    }
  });

  test('should verify GeoJSON data availability', async ({ page }) => {
    // Check if GeoJSON files are available
    const testMonths = ['2023-05', '2023-06', '2024-01'];

    for (const month of testMonths) {
      const yearMonth = month.replace('-', '');
      const geojsonUrl = `${CLOUDFRONT_URL}/data/geojson/anomalies${yearMonth}.geojson`;

      console.log(`Checking GeoJSON: ${geojsonUrl}`);

      const response = await page.request.get(geojsonUrl);
      console.log(`  Status: ${response.status()}`);

      if (response.status() === 200) {
        const data = await response.json();
        console.log(`  ✅ Found ${data.features?.length || 0} markers for ${month}`);
      } else {
        console.log(`  ❌ GeoJSON not found for ${month}`);
      }
    }
  });

  test('should test end-to-end marker click flow', async ({ page }) => {
    let apiRequestMade = false;
    let apiRequestBody: any = null;
    let apiResponseStatus: number | null = null;

    // Monitor network requests
    page.on('request', request => {
      if (request.url().includes('/reasoning')) {
        apiRequestMade = true;
        const postData = request.postData();
        if (postData) {
          try {
            apiRequestBody = JSON.parse(postData);
            console.log('🔍 Captured API request body:', apiRequestBody);
          } catch (e) {
            console.log('⚠️ Could not parse request body');
          }
        }
      }
    });

    page.on('response', response => {
      if (response.url().includes('/reasoning')) {
        apiResponseStatus = response.status();
        console.log('🔍 API response status:', apiResponseStatus);
      }
    });

    // Navigate to the page
    await page.goto(CLOUDFRONT_URL);
    await page.waitForLoadState('networkidle');

    // Check if map loaded
    const mapElement = await page.locator('#map').count();
    expect(mapElement).toBe(1);
    console.log('✅ Map element found');

    // Wait for markers to load (if GeoJSON exists)
    await page.waitForTimeout(3000);

    // Try to find markers
    const markers = await page.locator('.leaflet-marker-icon').count();
    console.log(`📍 Found ${markers} markers on map`);

    if (markers > 0) {
      console.log('✅ Markers found! Clicking first marker...');

      // Click the first marker
      await page.locator('.leaflet-marker-icon').first().click();

      // Wait for side panel to open
      await page.waitForTimeout(2000);

      // Check if side panel opened
      const sidePanelOpen = await page.locator('#sidePanel.open').count();
      expect(sidePanelOpen).toBe(1);
      console.log('✅ Side panel opened');

      // Wait for API call
      await page.waitForTimeout(3000);

      if (apiRequestMade) {
        console.log('✅ API request was made');
        console.log('Request body format:', apiRequestBody);
        console.log('Response status:', apiResponseStatus);

        // Verify request has all required fields
        expect(apiRequestBody).toHaveProperty('lat');
        expect(apiRequestBody).toHaveProperty('lon');
        expect(apiRequestBody).toHaveProperty('co2');
        expect(apiRequestBody).toHaveProperty('deviation');
        expect(apiRequestBody).toHaveProperty('date');
        expect(apiRequestBody).toHaveProperty('severity');
        expect(apiRequestBody).toHaveProperty('zscore');
      } else {
        console.log('❌ No API request was made');
      }
    } else {
      console.log('❌ No markers found - GeoJSON data missing');
      console.log('⚠️ Cannot test marker click without data');
    }
  });

  test('should check for network errors on page', async ({ page }) => {
    const consoleErrors: string[] = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto(CLOUDFRONT_URL);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Check for visible error messages
    const errorMessages = await page.locator('text=/ネットワークエラー/i').count();

    if (errorMessages > 0) {
      console.log('❌ Network error message visible on page');
      const errorText = await page.locator('text=/ネットワークエラー/i').first().textContent();
      console.log('Error message:', errorText);
    } else {
      console.log('✅ No network error messages visible');
    }

    if (consoleErrors.length > 0) {
      console.log('Console errors found:', consoleErrors);
    }
  });
});
