import { test, expect } from '@playwright/test';

const CLOUDFRONT_URL = 'https://dy0dc92sru60q.cloudfront.net';
const API_GATEWAY_URL = 'https://of1svnz3yk.execute-api.us-east-1.amazonaws.com/prod';

test.describe('Reasoning API Integration', () => {
  test('should successfully call reasoning API when clicking marker', async ({ page }) => {
    const apiRequests: any[] = [];
    const apiResponses: any[] = [];

    // Monitor API requests
    page.on('request', request => {
      if (request.url().includes('reasoning')) {
        console.log('📤 API Request:', {
          url: request.url(),
          method: request.method(),
          headers: request.headers(),
        });
        apiRequests.push({
          url: request.url(),
          method: request.method(),
          body: request.postData(),
        });
      }
    });

    // Monitor API responses
    page.on('response', async response => {
      if (response.url().includes('reasoning')) {
        const status = response.status();
        let body = null;
        try {
          body = await response.text();
        } catch (e) {
          body = 'Could not read response body';
        }

        console.log('📥 API Response:', {
          url: response.url(),
          status,
          statusText: response.statusText(),
          headers: response.headers(),
          body: body?.substring(0, 500),
        });

        apiResponses.push({
          url: response.url(),
          status,
          body,
        });
      }
    });

    // Go to the site
    await page.goto(CLOUDFRONT_URL);
    await page.waitForLoadState('networkidle');

    // Wait for map to load
    await page.waitForSelector('#map', { timeout: 10000 });
    console.log('✅ Map loaded');

    // Take screenshot before clicking
    await page.screenshot({ path: 'tests/screenshots/before-marker-click.png', fullPage: true });

    // Wait a bit for markers to be added to map
    await page.waitForTimeout(3000);

    // Try to find and click a marker
    // Leaflet markers are usually in .leaflet-marker-pane
    const markerPane = page.locator('.leaflet-marker-pane');
    const markers = markerPane.locator('img, canvas, path').first();

    if (await markers.count() > 0) {
      console.log('✅ Found marker, clicking...');
      await markers.click();

      // Wait for API call
      await page.waitForTimeout(5000);

      // Take screenshot after clicking
      await page.screenshot({ path: 'tests/screenshots/after-marker-click.png', fullPage: true });
    } else {
      console.log('⚠️ No markers found on map');
      // Try clicking on the map center instead
      const mapElement = page.locator('#map');
      await mapElement.click({ position: { x: 400, y: 300 } });
      await page.waitForTimeout(5000);
    }

    // Check if API was called
    console.log(`\n📊 API Requests made: ${apiRequests.length}`);
    console.log(`📊 API Responses received: ${apiResponses.length}`);

    if (apiRequests.length > 0) {
      console.log('\n✅ API Request Details:');
      console.log('URL:', apiRequests[0].url);
      console.log('Method:', apiRequests[0].method);
      console.log('Body:', apiRequests[0].body);
    }

    if (apiResponses.length > 0) {
      console.log('\n✅ API Response Details:');
      console.log('Status:', apiResponses[0].status);
      console.log('Body preview:', apiResponses[0].body?.substring(0, 200));

      // Verify successful response
      expect(apiResponses[0].status).toBeLessThan(500);
    }

    // Check for error messages in the page
    const pageContent = await page.content();
    if (pageContent.includes('ネットワークエラー')) {
      console.log('❌ Network error message found in page');
      console.log('API Requests:', apiRequests);
      console.log('API Responses:', apiResponses);
    }
  });

  test('should verify API endpoint is accessible', async ({ page }) => {
    // Try to call the API directly
    const apiUrl = `${API_GATEWAY_URL}/reasoning`;

    console.log(`Testing API endpoint: ${apiUrl}`);

    const response = await page.request.post(apiUrl, {
      data: {
        month: '2023-05',
        location: { lon: 139.7671, lat: 35.6812 },
        co2_value: 415.2,
        detection_days: 3,
        anomaly_rank: '高'
      },
      headers: {
        'Content-Type': 'application/json',
      },
    });

    console.log('Direct API call status:', response.status());
    console.log('Response headers:', response.headers());

    const responseBody = await response.text();
    console.log('Response body:', responseBody.substring(0, 500));

    // Verify response
    if (response.status() === 403) {
      console.log('⚠️ 403 Forbidden - Check CORS settings');
    } else if (response.status() === 404) {
      console.log('⚠️ 404 Not Found - Check API Gateway routing');
    } else if (response.status() >= 500) {
      console.log('⚠️ 5xx Server Error - Check Lambda function');
    }

    expect(response.status()).toBeLessThan(500);
  });
});
