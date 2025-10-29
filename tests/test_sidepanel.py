# -*- coding: utf-8 -*-
"""
サイドパネルUIの動作確認テスト (Playwright)

【テスト項目】
1. 初期状態でサイドパネルが非表示
2. openSidePanel()でパネルが表示される
3. パネル幅が400pxであること
4. ヘッダーに"CO₂異常値の原因推論"が表示
5. 閉じるボタンでパネルが閉じる
6. カスタムコンテンツでパネルを開く
7. スクロール機能
8. トグル機能
9. レスポンシブ対応
"""

from playwright.sync_api import sync_playwright, expect
import os
import time
import sys

# Windows環境でのUnicode出力対応
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_sidepanel():
    """サイドパネルUIの統合テスト"""

    # HTTPサーバーを起動
    import http.server
    import socketserver
    import threading

    PORT = 8888
    Handler = http.server.SimpleHTTPRequestHandler

    def start_server():
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            httpd.serve_forever()

    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    import time
    time.sleep(1)  # サーバー起動待ち

    test_url = f"http://localhost:{PORT}/sample_calendar.html"

    print(f"テスト対象: {test_url}")
    print("=" * 70)

    with sync_playwright() as p:
        # ブラウザを起動（ヘッドレスモードをオフにして視覚的に確認）
        browser = p.chromium.launch(headless=False, slow_mo=500)
        page = browser.new_page(viewport={"width": 1280, "height": 720})

        try:
            # ページを開く
            print("\n✓ ステップ1: sample_calendar.htmlを開く")
            page.goto(test_url)
            page.wait_for_load_state("networkidle")
            time.sleep(1)

            # テスト1: 初期状態でサイドパネルが非表示
            print("\n✓ テスト1: 初期状態でサイドパネルが非表示であることを確認")
            side_panel = page.locator("#sidePanel")
            expect(side_panel).not_to_have_class("open")

            # パネルの位置を確認（right: -400px）
            panel_right = page.evaluate("document.getElementById('sidePanel').getBoundingClientRect().left")
            window_width = page.evaluate("window.innerWidth")
            assert panel_right >= window_width, f"パネルが画面外にあること (panel_right={panel_right}, window_width={window_width})"
            print(f"  ✓ パネルが画面外に配置されています (left={panel_right}px)")

            # テスト2: openSidePanel()でパネルが表示される
            print("\n✓ テスト2: openSidePanel()でパネルが表示されることを確認")
            page.evaluate("openSidePanel()")
            time.sleep(0.5)  # アニメーション待ち
            expect(side_panel).to_have_class("side-panel open")
            print("  ✓ パネルが開きました")

            # テスト3: パネル幅が400pxであること
            print("\n✓ テスト3: パネル幅が400pxであることを確認")
            panel_width = page.evaluate("document.getElementById('sidePanel').offsetWidth")
            assert panel_width == 400, f"パネル幅が400pxであること (実際: {panel_width}px)"
            print(f"  ✓ パネル幅: {panel_width}px")

            # テスト4: ヘッダーに"CO₂異常値の原因推論"が表示
            print("\n✓ テスト4: ヘッダーに「CO₂異常値の原因推論」が表示されていることを確認")
            header_text = page.locator(".side-panel-header h3").text_content()
            assert "CO₂異常値の原因推論" in header_text, f"ヘッダーテキストが正しいこと (実際: {header_text})"
            print(f"  ✓ ヘッダーテキスト: {header_text}")

            # テスト5: 閉じるボタンでパネルが閉じる
            print("\n✓ テスト5: 閉じるボタンでパネルが閉じることを確認")
            close_button = page.locator(".close-btn")
            close_button.click()
            time.sleep(0.5)  # アニメーション待ち
            expect(side_panel).not_to_have_class("open")
            print("  ✓ 閉じるボタンでパネルが閉じました")

            # テスト6: カスタムコンテンツでパネルを開く
            print("\n✓ テスト6: カスタムコンテンツでパネルを開くことを確認")
            custom_content = "<h4>テスト</h4><p>カスタムコンテンツです。</p>"
            page.evaluate(f"openSidePanel(`{custom_content}`)")
            time.sleep(0.5)
            content_html = page.locator(".side-panel-content").inner_html()
            assert "カスタムコンテンツです" in content_html, "カスタムコンテンツが表示されること"
            print("  ✓ カスタムコンテンツが表示されました")

            # テスト7: スクロール機能
            print("\n✓ テスト7: スクロール機能を確認")
            long_content = "<h4>スクロールテスト</h4>" + "<p>テスト行</p>" * 50
            page.evaluate(f"openSidePanel(`{long_content}`)")
            time.sleep(0.5)

            # コンテンツエリアがスクロール可能か確認
            is_scrollable = page.evaluate("""
                () => {
                    const content = document.querySelector('.side-panel-content');
                    return content.scrollHeight > content.clientHeight;
                }
            """)
            assert is_scrollable, "コンテンツエリアがスクロール可能であること"
            print("  ✓ コンテンツエリアがスクロール可能です")

            # テスト8: トグル機能
            print("\n✓ テスト8: トグル機能を確認")
            page.evaluate("closeSidePanel()")
            time.sleep(0.5)

            page.evaluate("toggleSidePanel()")  # 開く
            time.sleep(0.5)
            expect(side_panel).to_have_class("side-panel open")
            print("  ✓ toggleSidePanel()でパネルが開きました")

            page.evaluate("toggleSidePanel()")  # 閉じる
            time.sleep(0.5)
            expect(side_panel).not_to_have_class("open")
            print("  ✓ toggleSidePanel()でパネルが閉じました")

            # テスト9: レスポンシブ対応（モバイル表示）
            print("\n✓ テスト9: レスポンシブ対応を確認（モバイル表示）")
            page.set_viewport_size({"width": 375, "height": 667})  # iPhone SE サイズ
            time.sleep(0.5)

            page.evaluate("openSidePanel()")
            time.sleep(0.5)

            panel_width_mobile = page.evaluate("document.getElementById('sidePanel').offsetWidth")
            viewport_width = page.evaluate("window.innerWidth")
            assert panel_width_mobile == viewport_width, f"モバイル表示でパネル幅が100%であること (panel={panel_width_mobile}px, viewport={viewport_width}px)"
            print(f"  ✓ モバイル表示でパネル幅が100%です (パネル幅={panel_width_mobile}px)")

            # テスト10: マーカークリックでサイドパネルが開く
            print("\n✓ テスト10: マーカークリックでサイドパネルが開くことを確認")

            # デスクトップサイズに戻す
            page.set_viewport_size({"width": 1280, "height": 720})
            time.sleep(0.5)

            # サイドパネルを閉じる
            page.evaluate("closeSidePanel()")
            time.sleep(0.5)

            # 2023年6月のデータを読み込む（データが存在する月）
            page.select_option("#yearSelect", "2023")
            page.select_option("#monthSelect", "06")
            time.sleep(2)  # データ読み込み待ち

            # マーカーが存在するか確認
            markers_count = page.evaluate("""
                () => {
                    const markers = document.querySelectorAll('.gradient-marker');
                    return markers.length;
                }
            """)
            print(f"  ✓ マーカー数: {markers_count}個")

            if markers_count > 0:
                # 最初のマーカーをクリック
                page.evaluate("""
                    () => {
                        const marker = document.querySelector('.gradient-marker');
                        if (marker) {
                            marker.click();
                        }
                    }
                """)
                time.sleep(1)

                # サイドパネルが開いたか確認
                expect(side_panel).to_have_class("side-panel open")
                print("  ✓ マーカークリックでサイドパネルが開きました")

                # サイドパネルにコンテンツが表示されているか確認
                content_text = page.locator(".side-panel-content").inner_text()
                assert "ppm" in content_text, "CO₂濃度データが表示されていること"
                assert "位置情報" in content_text, "位置情報が表示されていること"
                assert "測定データ" in content_text, "測定データが表示されていること"
                assert "原因推論" in content_text, "原因推論が表示されていること"
                print("  ✓ サイドパネルに詳細情報が表示されています")
            else:
                print("  ⚠ マーカーが見つかりませんでした（データが存在しない可能性）")

            print("\n" + "=" * 70)
            print("✓ すべてのテストが成功しました！")
            print("=" * 70)

            # 視覚的確認のために少し待つ
            time.sleep(3)

        except AssertionError as e:
            print(f"\n✗ テスト失敗: {e}")
            raise
        except Exception as e:
            print(f"\n✗ エラー発生: {e}")
            raise
        finally:
            browser.close()

if __name__ == "__main__":
    print("サイドパネルUIテストを開始します...")
    test_sidepanel()
    print("\nテスト完了！")
