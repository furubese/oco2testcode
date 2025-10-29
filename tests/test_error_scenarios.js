const { chromium } = require('playwright');

async function testNetworkError(page) {
  console.log('\n=== Test 1: Network Error (Server Down) ===');

  try {
    // Navigate to test error handling page
    await page.goto('http://localhost:5000/test_error_handling.html');
    await page.waitForTimeout(1000);

    // Click network error test button
    console.log('Clicking "ネットワークエラーをテスト" button...');
    await page.click('button:has-text("ネットワークエラーをテスト")');

    // Wait for result
    await page.waitForTimeout(3000);

    // Check result
    const resultText = await page.locator('#networkResult').textContent();
    console.log('Result:', resultText.substring(0, 150));

    if (resultText.includes('テスト成功') && resultText.includes('ネットワークエラー')) {
      console.log('✓ Network error test PASSED');
      return true;
    } else {
      console.log('✗ Network error test FAILED');
      return false;
    }
  } catch (error) {
    console.log('✗ Test error:', error.message);
    return false;
  }
}

async function test404Error(page) {
  console.log('\n=== Test 2: 404 Not Found Error ===');

  try {
    await page.goto('http://localhost:5000/test_error_handling.html');
    await page.waitForTimeout(1000);

    // Click 404 error test button
    console.log('Clicking "404エラーをテスト" button...');
    await page.click('button:has-text("404エラーをテスト")');

    // Wait for result
    await page.waitForTimeout(3000);

    // Check result
    const resultText = await page.locator('#error404Result').textContent();
    console.log('Result:', resultText.substring(0, 150));

    if (resultText.includes('テスト成功') && resultText.includes('APIエンドポイントが見つかりません')) {
      console.log('✓ 404 error test PASSED');
      return true;
    } else {
      console.log('✗ 404 error test FAILED');
      return false;
    }
  } catch (error) {
    console.log('✗ Test error:', error.message);
    return false;
  }
}

async function testNormalAPI(page) {
  console.log('\n=== Test 3: Normal API Request ===');

  try {
    await page.goto('http://localhost:5000/test_error_handling.html');
    await page.waitForTimeout(1000);

    // Click normal API test button
    console.log('Clicking "正常なAPIをテスト" button...');
    await page.click('button:has-text("正常なAPIをテスト")');

    // Wait for result
    await page.waitForTimeout(10000);  // Give more time for API

    // Check result
    const resultText = await page.locator('#normalResult').textContent();
    console.log('Result:', resultText.substring(0, 150));

    if (resultText.includes('テスト成功')) {
      console.log('✓ Normal API test PASSED');
      return true;
    } else {
      console.log('✗ Normal API test FAILED');
      console.log('Full result:', resultText);
      return false;
    }
  } catch (error) {
    console.log('✗ Test error:', error.message);
    return false;
  }
}

async function testErrorRecovery(page) {
  console.log('\n=== Test 4: Error Recovery (Multiple Requests) ===');

  try {
    await page.goto('http://localhost:5000');
    await page.waitForTimeout(2000);

    // Select year and month
    await page.selectOption('#yearSelect', '2023');
    await page.selectOption('#monthSelect', '06');
    await page.waitForTimeout(3000);

    const markers = await page.locator('.leaflet-marker-icon').count();
    console.log(`Found ${markers} markers`);

    if (markers < 2) {
      console.log('✗ Not enough markers for test');
      return false;
    }

    // Click first marker
    console.log('Clicking first marker...');
    await page.locator('.leaflet-marker-icon').first().click();
    await page.waitForTimeout(5000);

    // Check if panel opened
    let panelContent = await page.locator('.side-panel-content').textContent();
    const firstSuccess = panelContent.includes('AI原因推論') || panelContent.includes('CO₂');

    console.log(`First request: ${firstSuccess ? 'SUCCESS' : 'FAILED'}`);

    // Close panel
    await page.click('.close-btn');
    await page.waitForTimeout(1000);

    // Click second marker
    console.log('Clicking second marker...');
    await page.locator('.leaflet-marker-icon').nth(1).click();
    await page.waitForTimeout(5000);

    // Check if panel opened again
    panelContent = await page.locator('.side-panel-content').textContent();
    const secondSuccess = panelContent.includes('AI原因推論') || panelContent.includes('CO₂');

    console.log(`Second request: ${secondSuccess ? 'SUCCESS' : 'FAILED'}`);

    if (firstSuccess && secondSuccess) {
      console.log('✓ Error recovery test PASSED (both requests successful)');
      return true;
    } else {
      console.log('✗ Error recovery test FAILED');
      return false;
    }
  } catch (error) {
    console.log('✗ Test error:', error.message);
    return false;
  }
}

async function testLoadingIndicator(page) {
  console.log('\n=== Test 5: Loading Indicator ===');

  try {
    await page.goto('http://localhost:5000');
    await page.waitForTimeout(2000);

    // Select year and month
    await page.selectOption('#yearSelect', '2023');
    await page.selectOption('#monthSelect', '06');
    await page.waitForTimeout(3000);

    // Click first marker
    console.log('Clicking marker and checking loading indicator...');
    await page.locator('.leaflet-marker-icon').first().click();

    // Check if loading indicator appears immediately
    await page.waitForTimeout(100);
    const loadingDisplay = await page.locator('#loadingIndicator').evaluate(el => window.getComputedStyle(el).display);

    console.log(`Loading indicator display: ${loadingDisplay}`);

    if (loadingDisplay === 'flex') {
      console.log('✓ Loading indicator appears correctly');

      // Wait for loading to finish
      await page.waitForTimeout(5000);

      // Check if loading indicator is hidden
      const loadingDisplayAfter = await page.locator('#loadingIndicator').evaluate(el => window.getComputedStyle(el).display);

      if (loadingDisplayAfter === 'none') {
        console.log('✓ Loading indicator hides after request completes');
        return true;
      } else {
        console.log('✗ Loading indicator did not hide');
        return false;
      }
    } else {
      console.log('✗ Loading indicator did not appear (might have been too fast)');
      return false;
    }
  } catch (error) {
    console.log('✗ Test error:', error.message);
    return false;
  }
}

(async () => {
  console.log('╔════════════════════════════════════════════════════════════╗');
  console.log('║  Error Handling Test Suite with Playwright                ║');
  console.log('╚════════════════════════════════════════════════════════════╝\n');

  const browser = await chromium.launch({
    headless: false
  });

  const context = await browser.newContext();
  const page = await context.newPage();

  // Enable console logging
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log('Browser Error:', msg.text());
    }
  });

  const results = {
    networkError: false,
    error404: false,
    normalAPI: false,
    errorRecovery: false,
    loadingIndicator: false
  };

  // Run tests
  results.normalAPI = await testNormalAPI(page);
  results.networkError = await testNetworkError(page);
  results.error404 = await test404Error(page);
  results.errorRecovery = await testErrorRecovery(page);
  results.loadingIndicator = await testLoadingIndicator(page);

  // Take final screenshot
  await page.screenshot({ path: 'test_final_screenshot.png', fullPage: true });
  console.log('\nFinal screenshot saved: test_final_screenshot.png');

  // Print summary
  console.log('\n╔════════════════════════════════════════════════════════════╗');
  console.log('║  Test Summary                                              ║');
  console.log('╚════════════════════════════════════════════════════════════╝');

  const passed = Object.values(results).filter(r => r).length;
  const total = Object.values(results).length;

  console.log(`\nTests Passed: ${passed}/${total}`);
  console.log('\nDetailed Results:');
  console.log(`  1. Normal API Request:    ${results.normalAPI ? '✓ PASS' : '✗ FAIL'}`);
  console.log(`  2. Network Error:         ${results.networkError ? '✓ PASS' : '✗ FAIL'}`);
  console.log(`  3. 404 Error:             ${results.error404 ? '✓ PASS' : '✗ FAIL'}`);
  console.log(`  4. Error Recovery:        ${results.errorRecovery ? '✓ PASS' : '✗ FAIL'}`);
  console.log(`  5. Loading Indicator:     ${results.loadingIndicator ? '✓ PASS' : '✗ FAIL'}`);

  await browser.close();

  console.log('\n╔════════════════════════════════════════════════════════════╗');
  console.log('║  All Tests Complete!                                       ║');
  console.log('╚════════════════════════════════════════════════════════════╝\n');

  process.exit(passed === total ? 0 : 1);
})();
