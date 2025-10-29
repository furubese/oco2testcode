const { chromium } = require('playwright');

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function testNormalFlow(page) {
  console.log('\n=== Test 1: Normal Flow (API Working) ===');

  try {
    await page.goto('http://localhost:5000');
    await sleep(2000);

    // Select year and month
    console.log('Selecting 2023年6月...');
    await page.selectOption('#yearSelect', '2023');
    await page.selectOption('#monthSelect', '06');
    await sleep(3000);

    // Check markers loaded
    const markers = await page.locator('.leaflet-marker-icon').count();
    console.log(`Markers loaded: ${markers}`);

    if (markers === 0) {
      console.log('✗ No markers found');
      return false;
    }

    // Click first marker
    console.log('Clicking first marker...');
    await page.locator('.leaflet-marker-icon').first().click();

    // Check loading indicator appears
    await sleep(100);
    const loadingVisible = await page.locator('#loadingIndicator').isVisible();
    console.log(`Loading indicator visible: ${loadingVisible}`);

    // Wait for response
    await sleep(8000);

    // Check if panel opened and has content
    const panelOpen = await page.locator('#sidePanel').evaluate(el => el.classList.contains('open'));
    console.log(`Side panel open: ${panelOpen}`);

    if (!panelOpen) {
      console.log('✗ Side panel did not open');
      return false;
    }

    // Check content
    const content = await page.locator('.side-panel-content').textContent();

    if (content.includes('AI原因推論') || content.includes('Gemini')) {
      console.log('✓ Test PASSED: API response loaded successfully');
      console.log(`Content preview: ${content.substring(0, 100)}...`);

      // Check if loading indicator is hidden
      const loadingHidden = await page.locator('#loadingIndicator').evaluate(el => window.getComputedStyle(el).display === 'none');
      console.log(`Loading indicator hidden: ${loadingHidden}`);

      return true;
    } else if (content.includes('エラー') || content.includes('Error')) {
      console.log('✗ Test FAILED: Error message displayed');
      console.log(`Error content: ${content.substring(0, 200)}`);
      return false;
    } else {
      console.log('? Test UNCLEAR: Unexpected content');
      console.log(`Content: ${content.substring(0, 200)}`);
      return false;
    }
  } catch (error) {
    console.log(`✗ Test error: ${error.message}`);
    return false;
  }
}

async function testMultipleRequests(page) {
  console.log('\n=== Test 2: Multiple Requests (Error Recovery) ===');

  try {
    await page.goto('http://localhost:5000');
    await sleep(2000);

    // Select year and month
    await page.selectOption('#yearSelect', '2023');
    await page.selectOption('#monthSelect', '06');
    await sleep(3000);

    const markers = await page.locator('.leaflet-marker-icon').count();

    if (markers < 3) {
      console.log('✗ Not enough markers for test');
      return false;
    }

    let successCount = 0;

    // Test 3 different markers
    for (let i = 0; i < 3; i++) {
      console.log(`\nRequest ${i + 1}/3:`);

      // Click marker
      await page.locator('.leaflet-marker-icon').nth(i).click();
      await sleep(6000);

      // Check result
      const content = await page.locator('.side-panel-content').textContent();

      if (content.includes('AI原因推論') || content.includes('Gemini')) {
        console.log(`  ✓ Request ${i + 1} SUCCESS`);
        successCount++;
      } else {
        console.log(`  ✗ Request ${i + 1} FAILED`);
      }

      // Close panel
      await page.click('.close-btn');
      await sleep(500);
    }

    console.log(`\nSuccess rate: ${successCount}/3`);

    if (successCount === 3) {
      console.log('✓ Test PASSED: All requests successful');
      return true;
    } else if (successCount > 0) {
      console.log('⚠ Test PARTIAL: Some requests failed');
      return false;
    } else {
      console.log('✗ Test FAILED: All requests failed');
      return false;
    }
  } catch (error) {
    console.log(`✗ Test error: ${error.message}`);
    return false;
  }
}

async function testErrorDisplay(page, serverShouldBeRunning = true) {
  const testName = serverShouldBeRunning ? 'Normal Error Handling' : 'Network Error';
  console.log(`\n=== Test 3: Error Display (${testName}) ===`);

  if (!serverShouldBeRunning) {
    console.log('⚠ Please manually stop the Flask server now and press Enter...');
    console.log('  You have 10 seconds...');
    await sleep(10000);
  }

  try {
    await page.goto('http://localhost:5000');
    await sleep(2000);

    // Select year and month
    await page.selectOption('#yearSelect', '2023');
    await page.selectOption('#monthSelect', '06');
    await sleep(3000);

    // Click marker
    console.log('Clicking marker...');
    await page.locator('.leaflet-marker-icon').first().click();
    await sleep(5000);

    // Check for error message
    const content = await page.locator('.side-panel-content').textContent();

    if (content.includes('エラー') || content.includes('Error')) {
      console.log('✓ Test PASSED: Error message displayed');
      console.log(`Error message preview: ${content.substring(content.indexOf('エラー'), content.indexOf('エラー') + 100)}...`);

      // Check if loading is hidden
      const loadingHidden = await page.locator('#loadingIndicator').evaluate(el => window.getComputedStyle(el).display === 'none');
      console.log(`Loading indicator hidden after error: ${loadingHidden}`);

      return true;
    } else if (content.includes('AI原因推論')) {
      console.log('✗ Test FAILED: No error message (got success instead)');
      return false;
    } else {
      console.log('? Test UNCLEAR');
      return false;
    }
  } catch (error) {
    console.log(`✗ Test error: ${error.message}`);
    return false;
  }
}

async function testLoadingIndicator(page) {
  console.log('\n=== Test 4: Loading Indicator Behavior ===');

  try {
    await page.goto('http://localhost:5000');
    await sleep(2000);

    // Select year and month
    await page.selectOption('#yearSelect', '2023');
    await page.selectOption('#monthSelect', '06');
    await sleep(3000);

    // Click marker
    console.log('Clicking marker...');
    const clickPromise = page.locator('.leaflet-marker-icon').first().click();

    // Immediately check loading indicator
    await sleep(50);
    const loadingVisible = await page.locator('#loadingIndicator').isVisible();
    console.log(`Loading indicator appears: ${loadingVisible}`);

    await clickPromise;

    // Wait for request to complete
    await sleep(8000);

    // Check loading indicator is hidden
    const loadingHidden = await page.locator('#loadingIndicator').evaluate(el => window.getComputedStyle(el).display === 'none');
    console.log(`Loading indicator hidden after completion: ${loadingHidden}`);

    if (loadingVisible && loadingHidden) {
      console.log('✓ Test PASSED: Loading indicator works correctly');
      return true;
    } else {
      console.log('✗ Test FAILED: Loading indicator behavior incorrect');
      return false;
    }
  } catch (error) {
    console.log(`✗ Test error: ${error.message}`);
    return false;
  }
}

(async () => {
  console.log('╔════════════════════════════════════════════════════════════╗');
  console.log('║       Main App Error Handling Test Suite                  ║');
  console.log('╚════════════════════════════════════════════════════════════╝');

  const browser = await chromium.launch({
    headless: false,
    slowMo: 50  // Slow down for better visibility
  });

  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 }
  });

  const page = await context.newPage();

  // Enable console logging
  page.on('console', msg => {
    const type = msg.type();
    if (type === 'error' || type === 'warning') {
      console.log(`Browser ${type}:`, msg.text());
    }
  });

  const results = {};

  // Run tests
  console.log('\n📋 Running automated tests...\n');

  results.normalFlow = await testNormalFlow(page);
  await sleep(2000);

  results.multipleRequests = await testMultipleRequests(page);
  await sleep(2000);

  results.loadingIndicator = await testLoadingIndicator(page);
  await sleep(2000);

  // Take screenshot
  await page.screenshot({ path: 'test_results.png', fullPage: true });
  console.log('\n📸 Screenshot saved: test_results.png');

  // Print summary
  console.log('\n╔════════════════════════════════════════════════════════════╗');
  console.log('║  Test Summary                                              ║');
  console.log('╚════════════════════════════════════════════════════════════╝');

  const passed = Object.values(results).filter(r => r).length;
  const total = Object.values(results).length;

  console.log(`\nAutomated Tests: ${passed}/${total} passed\n`);
  console.log('Detailed Results:');
  console.log(`  1. Normal Flow:          ${results.normalFlow ? '✓ PASS' : '✗ FAIL'}`);
  console.log(`  2. Multiple Requests:    ${results.multipleRequests ? '✓ PASS' : '✗ FAIL'}`);
  console.log(`  3. Loading Indicator:    ${results.loadingIndicator ? '✓ PASS' : '✗ FAIL'}`);

  console.log('\n╔════════════════════════════════════════════════════════════╗');
  console.log('║  Manual Test Instructions                                  ║');
  console.log('╚════════════════════════════════════════════════════════════╝');
  console.log('\nPlease perform these manual tests:');
  console.log('\n1. Network Error Test:');
  console.log('   - Stop the Flask server (Ctrl+C)');
  console.log('   - Click a marker');
  console.log('   - Verify error message: "サーバーに接続できませんでした"');
  console.log('\n2. Timeout Test (if needed):');
  console.log('   - Modify Flask server to add artificial delay');
  console.log('   - Verify timeout after 30 seconds');
  console.log('\n3. Error Recovery Test:');
  console.log('   - Restart Flask server after step 1');
  console.log('   - Click another marker');
  console.log('   - Verify it works normally\n');

  console.log('Browser will stay open for 20 seconds for manual testing...\n');
  await sleep(20000);

  await browser.close();

  console.log('╔════════════════════════════════════════════════════════════╗');
  console.log('║  Tests Complete!                                           ║');
  console.log('╚════════════════════════════════════════════════════════════╝\n');

  process.exit(passed === total ? 0 : 1);
})();
