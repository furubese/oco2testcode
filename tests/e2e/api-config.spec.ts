import { test, expect } from '@playwright/test';

const CLOUDFRONT_URL = 'https://dy0dc92sru60q.cloudfront.net';
const EXPECTED_API_GATEWAY = 'https://of1svnz3yk.execute-api.us-east-1.amazonaws.com/prod/';

test.describe('CloudFront API Configuration', () => {
  test('should have correct API Gateway URL configured', async ({ page }) => {
    await page.goto(CLOUDFRONT_URL);
    await page.waitForLoadState('networkidle');

    const apiConfig = await page.evaluate(() => {
      return (window as any).APP_CONFIG;
    });

    console.log('Current API Configuration:', apiConfig);

    // Verify API Gateway URL is NOT localhost
    expect(apiConfig.API_GATEWAY_URL).not.toBe('http://localhost:5000');

    // Verify it's the correct production API Gateway URL
    expect(apiConfig.API_GATEWAY_URL).toBe(EXPECTED_API_GATEWAY);
  });

  test('should load config.js successfully', async ({ page }) => {
    let configLoaded = false;

    page.on('response', response => {
      if (response.url().includes('config.js')) {
        configLoaded = true;
        console.log('Config.js loaded:', response.url(), 'Status:', response.status());
      }
    });

    await page.goto(CLOUDFRONT_URL);
    await page.waitForLoadState('networkidle');

    expect(configLoaded).toBeTruthy();
  });

  test('should have APP_CONFIG available globally', async ({ page }) => {
    await page.goto(CLOUDFRONT_URL);
    await page.waitForLoadState('networkidle');

    const hasConfig = await page.evaluate(() => {
      return typeof (window as any).APP_CONFIG !== 'undefined';
    });

    expect(hasConfig).toBeTruthy();
  });

  test('should verify config.js content', async ({ page }) => {
    const response = await page.goto(`${CLOUDFRONT_URL}/config.js`);
    const configContent = await response?.text();

    console.log('Config.js content preview:', configContent?.substring(0, 300));

    // Check if it contains API_GATEWAY_URL
    expect(configContent).toContain('API_GATEWAY_URL');
    expect(configContent).toContain('ENDPOINTS');

    // Check current value
    if (configContent?.includes('localhost:5000')) {
      console.warn('⚠️  WARNING: API_GATEWAY_URL is still set to localhost:5000');
    } else if (configContent?.includes('execute-api.us-east-1.amazonaws.com')) {
      console.log('✅ API Gateway URL is correctly configured for AWS');
    }
  });
});
