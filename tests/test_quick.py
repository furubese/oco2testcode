"""
Quick test to verify the implementation works
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
    """Quick test"""
    print("=" * 80)
    print("タスク9: 推論結果の表示 - 簡易テスト")
    print("=" * 80)

    async with async_playwright() as p:
        # Launch browser
        print("\n[1] ブラウザを起動中...")
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # Navigate to page
        print("[2] ページを開く: http://localhost:5000")
        await page.goto('http://localhost:5000')
        await page.wait_for_timeout(2000)
        print("✓ ページが読み込まれました")

        # Take initial screenshot
        await page.screenshot(path='test_01_page_loaded.png')
        print("✓ スクリーンショット保存: test_01_page_loaded.png")

        # Select year and month
        print("\n[3] 年月を選択: 2023年6月")
        await page.select_option('#yearSelect', '2023')
        await page.select_option('#monthSelect', '06')
        await page.wait_for_timeout(3000)
        print("✓ 年月を選択しました")

        # Take screenshot after data load
        await page.screenshot(path='test_02_data_loaded.png')
        print("✓ スクリーンショット保存: test_02_data_loaded.png")

        # Check if markers appeared
        print("\n[4] マーカーの存在を確認中...")
        try:
            await page.wait_for_selector('.gradient-marker', timeout=5000)
            marker_count = await page.locator('.gradient-marker').count()
            print(f"✓ マーカーが見つかりました: {marker_count}個")
        except Exception as e:
            print(f"✗ マーカーが見つかりません: {e}")
            await browser.close()
            return False

        # Click first marker
        print("\n[5] 最初のマーカーをクリック...")
        marker = page.locator('.gradient-marker').first
        await marker.click()
        await page.wait_for_timeout(1000)
        print("✓ マーカーをクリックしました")

        # Check if side panel opened
        print("\n[6] サイドパネルが開いたか確認...")
        side_panel = page.locator('#sidePanel')
        panel_class = await side_panel.get_attribute('class')
        if 'open' in panel_class:
            print("✓ サイドパネルが開きました")
        else:
            print("✗ サイドパネルが開きませんでした")
            await browser.close()
            return False

        # Wait for loading to complete
        print("\n[7] 推論処理を待機中...")
        loading = page.locator('#loadingIndicator')
        try:
            await loading.wait_for(state='hidden', timeout=30000)
            print("✓ 推論が完了しました")
        except Exception as e:
            print(f"⚠ タイムアウト: {e}")

        await page.wait_for_timeout(2000)

        # Take screenshot of inference result
        await page.screenshot(path='test_03_inference_first.png')
        print("✓ スクリーンショット保存: test_03_inference_first.png")

        # Check if inference text is displayed
        print("\n[8] 推論結果の内容を確認...")
        content = page.locator('.side-panel-content')
        content_text = await content.inner_text()

        # Check for required fields
        required_fields = ['緯度:', '経度:', 'CO₂濃度', '偏差:', '観測日:', 'AI原因推論']
        missing = []
        for field in required_fields:
            if field not in content_text:
                missing.append(field)

        if missing:
            print(f"✗ 必須フィールドが見つかりません: {missing}")
        else:
            print(f"✓ すべての必須フィールドが表示されています")

        # Check for cache indicator (should NOT be present on first click)
        print("\n[9] キャッシュインジケーターを確認（初回クリック）...")
        if '（キャッシュ）' in content_text:
            print("✗ 初回クリックなのに「（キャッシュ）」が表示されています")
        else:
            print("✓ 初回クリックでは「（キャッシュ）」が表示されていません")

        # Close side panel
        print("\n[10] サイドパネルを閉じる...")
        close_btn = page.locator('.close-btn')
        await close_btn.click()
        await page.wait_for_timeout(500)
        print("✓ サイドパネルを閉じました")

        # Click same marker again
        print("\n[11] 同じマーカーを再度クリック...")
        await marker.click()
        await page.wait_for_timeout(1000)
        print("✓ マーカーを再クリックしました")

        # Wait for loading (should be fast with cache)
        try:
            await loading.wait_for(state='hidden', timeout=5000)
            print("✓ キャッシュから推論結果を取得しました（高速）")
        except:
            print("⚠ ローディング待機タイムアウト")

        await page.wait_for_timeout(2000)

        # Take screenshot of cached result
        await page.screenshot(path='test_04_inference_cached.png')
        print("✓ スクリーンショット保存: test_04_inference_cached.png")

        # Check for cache indicator (should be present on second click)
        print("\n[12] キャッシュインジケーターを確認（2回目クリック）...")
        content_text = await content.inner_text()
        if '（キャッシュ）' in content_text:
            print("✓ 2回目クリックで「（キャッシュ）」が表示されています")
        else:
            print("✗ 2回目クリックなのに「（キャッシュ）」が表示されていません")

        # Summary
        print("\n" + "=" * 80)
        print("テスト完了")
        print("=" * 80)
        print("\n保存されたスクリーンショット:")
        print("  1. test_01_page_loaded.png - ページ読み込み後")
        print("  2. test_02_data_loaded.png - データ読み込み後")
        print("  3. test_03_inference_first.png - 初回推論結果")
        print("  4. test_04_inference_cached.png - キャッシュ推論結果")
        print("\nブラウザは10秒後に閉じます...")

        await page.wait_for_timeout(10000)
        await browser.close()
        return True


if __name__ == '__main__':
    try:
        success = asyncio.run(main())
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
