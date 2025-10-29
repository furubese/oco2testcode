"""
Final comprehensive test with detailed logging
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
    """Final comprehensive test"""
    print("=" * 80)
    print("タスク9: 推論結果の表示 - 最終確認テスト")
    print("=" * 80)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # Enable console logging
        page.on('console', lambda msg: print(f"  [BROWSER] {msg.type}: {msg.text}"))
        page.on('pageerror', lambda err: print(f"  [ERROR] {err}"))

        print("\n[1] ページを開く...")
        await page.goto('http://localhost:5000')
        await page.wait_for_timeout(2000)
        print("✓ ページ読み込み完了")

        print("\n[2] 年月を選択...")
        await page.select_option('#yearSelect', '2023')
        await page.select_option('#monthSelect', '06')
        await page.wait_for_timeout(3000)
        print("✓ 2023年6月を選択")

        print("\n[3] マーカーを確認...")
        marker_count = await page.locator('.gradient-marker').count()
        print(f"✓ マーカー数: {marker_count}個")

        print("\n[4] 最初のマーカーをクリック...")
        marker = page.locator('.gradient-marker').first
        await marker.click()
        print("✓ クリック完了")

        print("\n[5] サイドパネルを待機...")
        await page.wait_for_selector('#sidePanel.open', timeout=5000)
        print("✓ サイドパネルが開きました")

        print("\n[6] 推論処理を待機（最大30秒）...")
        loading = page.locator('#loadingIndicator')
        try:
            await loading.wait_for(state='hidden', timeout=30000)
            print("✓ 推論完了")
        except:
            print("⚠ タイムアウト（30秒経過）")

        await page.wait_for_timeout(2000)

        print("\n[7] 1回目の結果を確認...")
        content = page.locator('.side-panel-content')
        text1 = await content.inner_text()

        if '🤖 AI原因推論' in text1:
            print("✓ AI原因推論セクションが見つかりました")
            if '（キャッシュ）' in text1:
                print("✗ 初回なのにキャッシュ表示あり")
            else:
                print("✓ 初回はキャッシュ表示なし")
        else:
            print("✗ AI原因推論セクションが見つかりません")
            print(f"  コンテンツ（最初の200文字）: {text1[:200]}")

        await page.screenshot(path='test_final_01_first.png')
        print("✓ スクリーンショット: test_final_01_first.png")

        print("\n[8] サイドパネルを閉じる...")
        await page.locator('.close-btn').click()
        await page.wait_for_timeout(1000)
        print("✓ サイドパネル閉じました")

        print("\n[9] 同じマーカーを再度クリック...")
        await marker.click()
        print("✓ 再クリック完了")

        print("\n[10] サイドパネル再表示を待機...")
        await page.wait_for_selector('#sidePanel.open', timeout=5000)
        print("✓ サイドパネル再表示")

        print("\n[11] キャッシュからの読み込みを待機（最大5秒）...")
        try:
            await loading.wait_for(state='hidden', timeout=5000)
            print("✓ 表示完了（キャッシュ利用想定）")
        except:
            print("⚠ タイムアウト")

        await page.wait_for_timeout(2000)

        print("\n[12] 2回目の結果を確認...")
        text2 = await content.inner_text()

        if '🤖 AI原因推論' in text2:
            print("✓ AI原因推論セクションが見つかりました")
            if '（キャッシュ）' in text2:
                print("✓ 2回目はキャッシュ表示あり")
            else:
                print("✗ 2回目なのにキャッシュ表示なし")
                print(f"  コンテンツ（最初の500文字）: {text2[:500]}")
        else:
            print("✗ AI原因推論セクションが見つかりません")
            print(f"  コンテンツ全体: {text2}")

        await page.screenshot(path='test_final_02_cached.png')
        print("✓ スクリーンショット: test_final_02_cached.png")

        print("\n" + "=" * 80)
        print("テスト完了")
        print("=" * 80)
        print("\nブラウザは10秒後に閉じます...")

        await page.wait_for_timeout(10000)
        await browser.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n✗ エラー: {e}")
        import traceback
        traceback.print_exc()
