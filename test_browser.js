const { chromium } = require('playwright');

(async () => {
  console.log('Starting browser test...\n');

  // Launch browser
  const browser = await chromium.launch({
    headless: false  // Set to true for headless mode
  });

  const context = await browser.newContext();
  const page = await context.newPage();

  // Enable console logging
  page.on('console', msg => console.log('Browser Console:', msg.text()));

  // Navigate to the app
  console.log('Navigating to http://localhost:5000...');
  await page.goto('http://localhost:5000');

  // Wait for map to load
  console.log('Waiting for map to load...');
  await page.waitForTimeout(2000);

  // Check if year select exists
  const yearSelect = await page.locator('#yearSelect').count();
  console.log(`Year select found: ${yearSelect > 0}`);

  if (yearSelect > 0) {
    // Select 2023年6月
    console.log('Selecting 2023年6月...');
    await page.selectOption('#yearSelect', '2023');
    await page.selectOption('#monthSelect', '06');

    // Wait for data to load
    await page.waitForTimeout(3000);

    // Check if markers are loaded
    const status = await page.locator('#status').textContent();
    console.log(`Status: ${status}`);

    // Try to find and click a marker
    console.log('Looking for markers...');
    const markers = await page.locator('.leaflet-marker-icon').count();
    console.log(`Markers found: ${markers}`);

    if (markers > 0) {
      console.log('Clicking first marker...');
      await page.locator('.leaflet-marker-icon').first().click();

      // Wait for side panel to open
      await page.waitForTimeout(2000);

      // Check if side panel opened
      const sidePanel = await page.locator('#sidePanel').getAttribute('class');
      console.log(`Side panel classes: ${sidePanel}`);

      if (sidePanel && sidePanel.includes('open')) {
        console.log('✓ Side panel opened successfully');

        // Wait for loading to complete
        await page.waitForTimeout(5000);

        // Check for error or success
        const panelContent = await page.locator('.side-panel-content').textContent();

        if (panelContent.includes('ネットワークエラー') || panelContent.includes('タイムアウトエラー') || panelContent.includes('エラー')) {
          console.log('✗ Error displayed in panel (this might be expected if testing error scenarios)');
          console.log('Panel content preview:', panelContent.substring(0, 200));
        } else if (panelContent.includes('AI原因推論') || panelContent.includes('CO₂')) {
          console.log('✓ Success! Panel content loaded correctly');
        }

        // Take screenshot
        await page.screenshot({ path: 'test_screenshot_success.png' });
        console.log('Screenshot saved: test_screenshot_success.png');
      } else {
        console.log('✗ Side panel did not open');
      }
    } else {
      console.log('✗ No markers found. Check if GeoJSON data is loaded.');
    }
  }

  // Test error handling by stopping server
  console.log('\n--- Testing Network Error ---');
  console.log('To test network error:');
  console.log('1. Stop the Flask server');
  console.log('2. Click another marker');
  console.log('3. You should see a network error message');

  // Keep browser open for manual testing
  console.log('\nBrowser will stay open for 30 seconds for manual testing...');
  console.log('You can now manually test error scenarios:');
  console.log('- Click markers to test API calls');
  console.log('- Stop Flask server and click markers to test network errors');

  await page.waitForTimeout(30000);

  await browser.close();
  console.log('\nTest complete!');
})();
