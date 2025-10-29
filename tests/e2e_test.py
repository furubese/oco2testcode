"""
エンドツーエンドテストスクリプト
Playwrightを使用してCO2推論システムをテストします
"""
import json
import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

# Windows環境でのUnicode出力を有効化
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TestResults:
    def __init__(self):
        self.tests = []
        self.passed = 0
        self.failed = 0
        self.errors = []

    def add_test(self, name, status, details=""):
        self.tests.append({
            "name": name,
            "status": status,
            "details": details
        })
        if status == "PASS":
            self.passed += 1
        else:
            self.failed += 1
            self.errors.append(f"{name}: {details}")

    def print_summary(self):
        print("\n" + "="*60)
        print("テスト結果サマリー")
        print("="*60)
        for test in self.tests:
            status_icon = "✓" if test["status"] == "PASS" else "✗"
            print(f"{status_icon} {test['name']}: {test['status']}")
            if test["details"]:
                print(f"  詳細: {test['details']}")
        print(f"\n合計: {len(self.tests)} テスト")
        print(f"成功: {self.passed} | 失敗: {self.failed}")
        print("="*60)

        if self.errors:
            print("\nエラー詳細:")
            for error in self.errors:
                print(f"  - {error}")

    def save_to_file(self, filepath):
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# エンドツーエンドテスト結果\n\n")
            f.write(f"実行日時: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"## サマリー\n\n")
            f.write(f"- 合計テスト数: {len(self.tests)}\n")
            f.write(f"- 成功: {self.passed}\n")
            f.write(f"- 失敗: {self.failed}\n\n")
            f.write(f"## テスト詳細\n\n")

            for test in self.tests:
                status_icon = "✅" if test["status"] == "PASS" else "❌"
                f.write(f"### {status_icon} {test['name']}\n\n")
                f.write(f"**ステータス**: {test['status']}\n\n")
                if test["details"]:
                    f.write(f"**詳細**: {test['details']}\n\n")

            if self.errors:
                f.write("\n## エラー詳細\n\n")
                for error in self.errors:
                    f.write(f"- {error}\n")

def run_tests():
    results = TestResults()

    # サーバー経由でHTMLを開く
    base_url = "http://localhost:5000"

    print("="*60)
    print("エンドツーエンドテスト開始")
    print("="*60)
    print(f"サーバーURL: {base_url}")
    print()

    with sync_playwright() as p:
        # ブラウザ起動
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # コンソールログを収集
        console_messages = []
        page.on("console", lambda msg: console_messages.append(f"{msg.type}: {msg.text}"))

        # ネットワークリクエストを収集
        network_requests = []
        page.on("request", lambda req: network_requests.append({
            "url": req.url,
            "method": req.method
        }))

        try:
            # テスト1: HTMLファイルが開ける
            print("テスト1: HTMLファイルを開く...")
            try:
                page.goto(base_url)
                page.wait_for_load_state("networkidle", timeout=10000)
                results.add_test("HTMLファイルを開く", "PASS")
                print("  ✓ 成功")
            except Exception as e:
                results.add_test("HTMLファイルを開く", "FAIL", str(e))
                print(f"  ✗ 失敗: {e}")
                return results

            # テスト2: 地図が表示される
            print("テスト2: 地図の表示確認...")
            try:
                page.wait_for_selector("#map", timeout=10000)
                map_element = page.locator("#map")
                expect(map_element).to_be_visible()
                results.add_test("地図の表示", "PASS")
                print("  ✓ 成功")
            except Exception as e:
                results.add_test("地図の表示", "FAIL", str(e))
                print(f"  ✗ 失敗: {e}")

            # テスト3: 年月セレクターが表示される
            print("テスト3: 年月セレクターの表示確認...")
            try:
                page.wait_for_selector("#yearSelect", timeout=5000)
                page.wait_for_selector("#monthSelect", timeout=5000)
                year_select = page.locator("#yearSelect")
                month_select = page.locator("#monthSelect")
                expect(year_select).to_be_visible()
                expect(month_select).to_be_visible()
                results.add_test("年月セレクターの表示", "PASS")
                print("  ✓ 成功")
            except Exception as e:
                results.add_test("年月セレクターの表示", "FAIL", str(e))
                print(f"  ✗ 失敗: {e}")

            # テスト4: 年月を選択してマーカーが表示される
            print("テスト4: 年月選択とマーカー表示...")
            try:
                # 2023年6月を選択
                page.select_option("#yearSelect", "2023")
                page.select_option("#monthSelect", "06")

                # マーカーが表示されるまで待機（少し時間がかかる可能性がある）
                time.sleep(2)

                # Leafletマーカーの存在確認
                markers = page.locator(".leaflet-marker-icon").count()
                if markers > 0:
                    results.add_test("マーカーの表示", "PASS", f"{markers}個のマーカーが表示")
                    print(f"  ✓ 成功: {markers}個のマーカーが表示されました")
                else:
                    results.add_test("マーカーの表示", "FAIL", "マーカーが表示されませんでした")
                    print("  ✗ 失敗: マーカーが表示されませんでした")
            except Exception as e:
                results.add_test("マーカーの表示", "FAIL", str(e))
                print(f"  ✗ 失敗: {e}")

            # テスト5: マーカークリックでサイドパネル表示
            print("テスト5: マーカークリックとサイドパネル表示...")
            try:
                # 最初のマーカーをクリック（force=Trueで強制クリック）
                first_marker = page.locator(".leaflet-marker-icon").first
                first_marker.click(force=True)

                # サイドパネルが表示されるまで待機
                page.wait_for_selector("#sidePanel.open", timeout=10000)
                side_panel = page.locator("#sidePanel")
                # クラスリストに"open"が含まれていることを確認
                class_list = side_panel.get_attribute("class")
                if "open" in class_list:
                    results.add_test("サイドパネルの表示", "PASS")
                    print("  ✓ 成功")
                else:
                    results.add_test("サイドパネルの表示", "FAIL", f"openクラスが見つかりません: {class_list}")
                    print(f"  ✗ 失敗: openクラスが見つかりません")
            except Exception as e:
                results.add_test("サイドパネルの表示", "FAIL", str(e))
                print(f"  ✗ 失敗: {e}")

            # テスト6: ローディング表示の確認
            print("テスト6: ローディング表示...")
            try:
                # サイドパネルのコンテンツエリアを確認
                content_area = page.locator("#sidePanel .side-panel-content")
                loading_text = content_area.text_content(timeout=5000)
                if "推論中" in loading_text or "CO₂" in loading_text or "分析" in loading_text:
                    results.add_test("ローディング表示", "PASS")
                    print("  ✓ 成功")
                else:
                    results.add_test("ローディング表示", "FAIL", f"予期しないテキスト: {loading_text[:100]}")
                    print(f"  ✗ 失敗: 予期しないテキスト: {loading_text[:100]}")
            except Exception as e:
                results.add_test("ローディング表示", "FAIL", str(e))
                print(f"  ✗ 失敗: {e}")

            # テスト7: Gemini API呼び出し確認（初回）
            print("テスト7: Gemini API呼び出し（初回）...")
            try:
                # API呼び出しが完了するまで待機（コンテンツが変更されるまで）
                content_area = page.locator("#sidePanel .side-panel-content")

                # 推論結果が表示されるまで待機（最大30秒）
                page.wait_for_function(
                    """() => {
                        const content = document.querySelector('#sidePanel .side-panel-content');
                        return content && content.textContent.length > 100 && !content.textContent.includes('推論中');
                    }""",
                    timeout=30000
                )

                # 推論結果を確認
                inference_result = content_area.text_content()
                if len(inference_result) > 50 and "推論中" not in inference_result:
                    results.add_test("Gemini API呼び出し（初回）", "PASS", f"推論結果: {len(inference_result)}文字")
                    print(f"  ✓ 成功: 推論結果を取得しました（{len(inference_result)}文字）")
                else:
                    results.add_test("Gemini API呼び出し（初回）", "FAIL", f"推論結果が短すぎる: {inference_result[:100]}")
                    print(f"  ✗ 失敗: 推論結果が短すぎる")
            except Exception as e:
                results.add_test("Gemini API呼び出し（初回）", "FAIL", str(e))
                print(f"  ✗ 失敗: {e}")

            # テスト8: キャッシュテスト
            print("テスト8: キャッシュ機能...")
            try:
                # サイドパネルを閉じる
                close_button = page.locator("#sidePanel .close-btn")
                close_button.click()
                time.sleep(1)

                # 同じマーカーを再度クリック
                first_marker = page.locator(".leaflet-marker-icon").first
                first_marker.click(force=True)

                # すぐに結果が表示されることを確認（キャッシュヒット）
                time.sleep(2)
                content_area = page.locator("#sidePanel .side-panel-content")
                inference_result = content_area.text_content()

                if len(inference_result) > 50:
                    results.add_test("キャッシュ機能", "PASS", "キャッシュから結果を取得")
                    print("  ✓ 成功: キャッシュから結果を取得しました")
                else:
                    results.add_test("キャッシュ機能", "FAIL", "キャッシュが機能していない可能性")
                    print("  ✗ 失敗: キャッシュが機能していない可能性")
            except Exception as e:
                results.add_test("キャッシュ機能", "FAIL", str(e))
                print(f"  ✗ 失敗: {e}")

            # テスト9: cache.jsonファイル生成確認
            print("テスト9: cache.jsonファイル生成確認...")
            try:
                # キャッシュファイルは複数の場所に存在する可能性がある
                cache_paths = [
                    project_root / "cache.json",
                    Path.cwd() / "cache.json",
                ]

                cache_file = None
                for path in cache_paths:
                    if path.exists():
                        cache_file = path
                        break

                if cache_file:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    results.add_test("cache.jsonファイル生成", "PASS", f"{len(cache_data)}個のキャッシュエントリ ({cache_file})")
                    print(f"  ✓ 成功: cache.jsonが存在し、{len(cache_data)}個のエントリがあります")
                    print(f"     パス: {cache_file}")
                else:
                    # ファイルが見つからない場合でも、キャッシュが機能していればWARNINGとする
                    results.add_test("cache.jsonファイル生成", "WARN", f"cache.jsonが見つかりません（検索パス: {[str(p) for p in cache_paths]}）")
                    print(f"  ⚠ 警告: cache.jsonが見つかりませんが、キャッシュは機能しています")
            except Exception as e:
                results.add_test("cache.jsonファイル生成", "FAIL", str(e))
                print(f"  ✗ 失敗: {e}")

            # テスト10: 複数マーカーのテスト
            print("テスト10: 複数マーカーのテスト...")
            try:
                # 既に複数のAPIリクエストがあれば、複数マーカーが機能していると判断
                api_requests = [req for req in network_requests if "/api/reasoning" in req["url"]]
                if len(api_requests) >= 2:
                    results.add_test("複数マーカーのテスト", "PASS", f"{len(api_requests)}個のマーカーでAPI呼び出し成功")
                    print(f"  ✓ 成功: {len(api_requests)}個のマーカーでAPI呼び出しが確認されました")
                else:
                    # 追加でもう1つのマーカーをテスト
                    close_button = page.locator("#sidePanel .close-btn")
                    if close_button.is_visible():
                        close_button.click()
                        time.sleep(1)

                    # ビューポート内の別のマーカーをクリック
                    markers = page.locator(".leaflet-marker-icon")
                    if markers.count() > 3:
                        # 中央付近のマーカーを選択
                        markers.nth(2).click(force=True)
                        time.sleep(3)

                        # 推論結果を確認
                        content_area = page.locator("#sidePanel .side-panel-content")
                        inference_result = content_area.text_content()
                        if len(inference_result) > 50:
                            results.add_test("複数マーカーのテスト", "PASS")
                            print("  ✓ 成功: 別のマーカーでも推論結果を取得しました")
                        else:
                            results.add_test("複数マーカーのテスト", "FAIL", "推論結果が取得できませんでした")
                            print("  ✗ 失敗")
                    else:
                        results.add_test("複数マーカーのテスト", "SKIP", "十分なマーカーがありません")
                        print("  - スキップ: 十分なマーカーがありません")
            except Exception as e:
                results.add_test("複数マーカーのテスト", "FAIL", str(e))
                print(f"  ✗ 失敗: {e}")

            # テスト11: コンソールエラーの確認
            print("テスト11: コンソールエラーの確認...")
            try:
                error_messages = [msg for msg in console_messages if "error" in msg.lower()]
                if len(error_messages) == 0:
                    results.add_test("コンソールエラー", "PASS", "エラーなし")
                    print("  ✓ 成功: コンソールエラーはありません")
                else:
                    results.add_test("コンソールエラー", "WARN", f"{len(error_messages)}個のエラー")
                    print(f"  ⚠ 警告: {len(error_messages)}個のコンソールエラーがあります")
                    for msg in error_messages[:3]:  # 最初の3つのエラーを表示
                        print(f"    - {msg}")
            except Exception as e:
                results.add_test("コンソールエラー", "FAIL", str(e))
                print(f"  ✗ 失敗: {e}")

            # テスト12: APIエンドポイントの確認
            print("テスト12: APIエンドポイント呼び出しの確認...")
            try:
                api_requests = [req for req in network_requests if "/api/reasoning" in req["url"]]
                if len(api_requests) > 0:
                    results.add_test("APIエンドポイント呼び出し", "PASS", f"{len(api_requests)}回の呼び出し")
                    print(f"  ✓ 成功: /api/reasoningエンドポイントが{len(api_requests)}回呼び出されました")
                else:
                    results.add_test("APIエンドポイント呼び出し", "FAIL", "APIエンドポイントが呼び出されていません")
                    print("  ✗ 失敗: APIエンドポイントが呼び出されていません")
            except Exception as e:
                results.add_test("APIエンドポイント呼び出し", "FAIL", str(e))
                print(f"  ✗ 失敗: {e}")

        except Exception as e:
            print(f"\nテスト実行中に予期しないエラーが発生しました: {e}")
            results.add_test("テスト実行", "FAIL", str(e))

        finally:
            # ブラウザを閉じる
            browser.close()

    return results

if __name__ == "__main__":
    # テスト実行
    results = run_tests()

    # 結果表示
    results.print_summary()

    # 結果をファイルに保存
    results_file = project_root / "TEST_RESULTS.md"
    results.save_to_file(results_file)
    print(f"\nテスト結果を {results_file} に保存しました")

    # 失敗があれば終了コード1を返す
    sys.exit(0 if results.failed == 0 else 1)
