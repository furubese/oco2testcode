"""
Simple test to verify inference display works
"""

import asyncio
import sys
import io
from playwright.async_api import async_playwright

# Fix Windows console encoding issues
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


async def main():
    """Simple manual test"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        print("Opening page...")
        import os
        html_path = os.path.abspath('sample_calendar.html')
        await page.goto(f'file:///{html_path}')

        print("Page loaded. Waiting for 5 seconds...")
        await page.wait_for_timeout(5000)

        print("Taking initial screenshot...")
        await page.screenshot(path='screenshot_01_initial.png')

        print("\nPlease manually:")
        print("1. Select year 2023, month June")
        print("2. Click on a marker")
        print("3. Verify that inference results are displayed")
        print("4. Check if '（キャッシュ）' appears on second click")
        print("\nPress Enter when done...")

        # Keep browser open
        await page.wait_for_timeout(60000)  # Wait 60 seconds

        print("Taking final screenshot...")
        await page.screenshot(path='screenshot_02_final.png')

        await browser.close()
        print("\nScreenshots saved:")
        print("- screenshot_01_initial.png")
        print("- screenshot_02_final.png")


if __name__ == '__main__':
    asyncio.run(main())
