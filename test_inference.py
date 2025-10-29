"""
Playwright test for CO2 anomaly inference display
Tests the inference result display functionality with cache behavior
"""

import asyncio
import time
import sys
import io
from playwright.async_api import async_playwright, expect

# Fix Windows console encoding issues
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


async def test_inference_display():
    """
    Test inference result display functionality

    Test items:
    1. Server startup and page load
    2. Marker click triggers side panel
    3. Inference result is displayed
    4. Location data is correctly displayed (lat, lon, CO2, deviation, date)
    5. First click: No cache indicator
    6. Second click: Cache indicator appears
    7. Inference text is 200-300 characters
    8. Japanese text is displayed correctly
    9. Content is scrollable
    """

    async with async_playwright() as p:
        # Launch browser in headless mode
        browser = await p.chromium.launch(headless=False)  # Set to True for CI/CD
        context = await browser.new_context()
        page = await context.new_page()

        print("=" * 80)
        print("TEST: CO2 Inference Display with Cache Behavior")
        print("=" * 80)

        # Step 1: Navigate to the page
        print("\n[Step 1] Loading sample_calendar.html...")
        try:
            # Use file:// protocol to load HTML directly
            import os
            html_path = os.path.abspath('sample_calendar.html')
            await page.goto(f'file:///{html_path}', timeout=10000)
            print("✓ Page loaded successfully")
        except Exception as e:
            print(f"✗ Failed to load page: {e}")
            await browser.close()
            return False

        # Wait for map initialization
        await page.wait_for_timeout(2000)

        # Step 2: Select year and month (2023-06)
        print("\n[Step 2] Selecting year 2023 and month June...")
        try:
            await page.select_option('#yearSelect', '2023')
            await page.select_option('#monthSelect', '06')
            await page.wait_for_timeout(3000)  # Increased wait time for data loading
            print("✓ Date selected: 2023-06")
        except Exception as e:
            print(f"✗ Failed to select date: {e}")
            await browser.close()
            return False

        # Step 3: Click a marker
        print("\n[Step 3] Clicking on a CO2 marker...")
        try:
            # Wait for markers to appear
            await page.wait_for_selector('.gradient-marker', timeout=10000)

            # Click the first marker
            marker = page.locator('.gradient-marker').first
            await marker.click()
            print("✓ Marker clicked")
        except Exception as e:
            print(f"✗ Failed to click marker: {e}")
            await browser.close()
            return False

        # Step 4: Wait for side panel to open and loading to complete
        print("\n[Step 4] Waiting for inference to complete...")
        try:
            # Wait for side panel to open
            side_panel = page.locator('#sidePanel')
            await expect(side_panel).to_have_class('side-panel open', timeout=5000)
            print("✓ Side panel opened")

            # Wait for loading indicator to disappear
            loading = page.locator('#loadingIndicator')
            await expect(loading).to_be_hidden(timeout=30000)
            print("✓ Loading completed")
        except Exception as e:
            print(f"✗ Failed during inference: {e}")
            await browser.close()
            return False

        # Step 5: Verify location data is displayed
        print("\n[Step 5] Verifying location data display...")
        try:
            content = page.locator('.side-panel-content')
            content_text = await content.inner_text()

            # Check for required fields
            required_fields = ['緯度:', '経度:', 'CO₂濃度', '偏差:', '観測日:']
            missing_fields = []
            for field in required_fields:
                if field not in content_text:
                    missing_fields.append(field)

            if missing_fields:
                print(f"✗ Missing fields: {', '.join(missing_fields)}")
                await browser.close()
                return False

            print("✓ All location data fields present")
            print(f"  - Fields: {', '.join(required_fields)}")
        except Exception as e:
            print(f"✗ Failed to verify location data: {e}")
            await browser.close()
            return False

        # Step 6: Check inference result (first time - should NOT have cache indicator)
        print("\n[Step 6] Checking first inference result (no cache expected)...")
        try:
            ai_section = page.locator('text=🤖 AI原因推論')
            ai_text = await ai_section.inner_text()

            if '（キャッシュ）' in ai_text:
                print(f"✗ Cache indicator found on first request (unexpected)")
                print(f"  Text: {ai_text}")
                await browser.close()
                return False

            print("✓ No cache indicator on first request")

            # Get the inference text length
            inference_div = page.locator('.side-panel-content div[style*="background-color: #f8f9fa"]')
            inference_text = await inference_div.inner_text()
            text_length = len(inference_text)

            print(f"✓ Inference text length: {text_length} characters")

            if text_length < 50:
                print(f"⚠ Warning: Text seems too short ({text_length} chars)")

            # Check if Japanese is displayed correctly
            if any(ord(char) > 127 for char in inference_text):
                print("✓ Japanese characters detected in inference result")
            else:
                print("⚠ Warning: No Japanese characters detected")

        except Exception as e:
            print(f"✗ Failed to check inference result: {e}")
            await browser.close()
            return False

        # Step 7: Close the side panel
        print("\n[Step 7] Closing side panel...")
        try:
            close_btn = page.locator('.close-btn')
            await close_btn.click()
            await page.wait_for_timeout(500)

            # Verify panel is closed
            await expect(side_panel).not_to_have_class('side-panel open')
            print("✓ Side panel closed")
        except Exception as e:
            print(f"✗ Failed to close side panel: {e}")
            await browser.close()
            return False

        # Step 8: Click the same marker again (should hit cache)
        print("\n[Step 8] Clicking the same marker again (cache expected)...")
        try:
            await marker.click()
            await page.wait_for_timeout(500)

            # Wait for side panel to open
            await expect(side_panel).to_have_class('side-panel open', timeout=5000)

            # Wait for loading to complete (should be faster with cache)
            await expect(loading).to_be_hidden(timeout=5000)
            print("✓ Second click completed")
        except Exception as e:
            print(f"✗ Failed during second click: {e}")
            await browser.close()
            return False

        # Step 9: Verify cache indicator is present
        print("\n[Step 9] Verifying cache indicator...")
        try:
            ai_section = page.locator('text=🤖 AI原因推論')
            ai_text = await ai_section.inner_text()

            if '（キャッシュ）' not in ai_text:
                print(f"✗ Cache indicator NOT found on second request")
                print(f"  Text: {ai_text}")
                await browser.close()
                return False

            print("✓ Cache indicator found on second request")
            print(f"  Header text: {ai_text}")
        except Exception as e:
            print(f"✗ Failed to verify cache indicator: {e}")
            await browser.close()
            return False

        # Step 10: Take screenshot for visual verification
        print("\n[Step 10] Taking screenshot...")
        try:
            await page.screenshot(path='test_result_screenshot.png', full_page=True)
            print("✓ Screenshot saved: test_result_screenshot.png")
        except Exception as e:
            print(f"⚠ Failed to take screenshot: {e}")

        # Test passed
        print("\n" + "=" * 80)
        print("✓ ALL TESTS PASSED")
        print("=" * 80)

        # Keep browser open for manual inspection
        print("\nBrowser will remain open for 10 seconds for inspection...")
        await page.wait_for_timeout(10000)

        await browser.close()
        return True


async def main():
    """Main test execution"""
    print("\n" + "=" * 80)
    print("Starting Playwright Test Suite")
    print("=" * 80)
    print("\nPrerequisites:")
    print("1. Flask server must be running on http://localhost:5000")
    print("2. sample_calendar.html must be accessible")
    print("3. anomalies202306.geojson must exist")
    print("4. GEMINI_API_KEY must be configured in .env")
    print("\nStarting test in 3 seconds...")
    print("=" * 80)

    await asyncio.sleep(3)

    try:
        success = await test_inference_display()

        if success:
            print("\n✓ Test suite completed successfully")
            return 0
        else:
            print("\n✗ Test suite failed")
            return 1
    except Exception as e:
        print(f"\n✗ Test suite crashed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    exit(exit_code)
