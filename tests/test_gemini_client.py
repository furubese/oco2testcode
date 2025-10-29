"""
gemini_client.py のテストスクリプト
"""

import os
import sys
from gemini_client import (
    load_api_key,
    generate_prompt,
    call_gemini_api,
    generate_inference,
    GeminiAPIError
)


def test_api_key_error():
    """Test 4: APIキー未設定時のエラーハンドリング"""
    print("Test 4: Testing API key error handling...")

    # 環境変数を一時的に削除
    original_key = os.environ.get('GEMINI_API_KEY')
    if 'GEMINI_API_KEY' in os.environ:
        del os.environ['GEMINI_API_KEY']

    try:
        load_api_key()
        print("  FAILED: Should have raised GeminiAPIError")
        return False
    except GeminiAPIError as e:
        print(f"  PASSED: Error correctly raised: {e}")
        return True
    finally:
        # 元の値を復元
        if original_key:
            os.environ['GEMINI_API_KEY'] = original_key


def test_prompt_generation():
    """Test 5: プロンプト生成テスト"""
    print("\nTest 5: Testing prompt generation...")

    sample_data = {
        "lat": 35.6762,
        "lon": 139.6503,
        "co2": 420.5,
        "deviation": 5.2,
        "date": "2023-01-15",
        "severity": "high",
        "zscore": 2.8
    }

    try:
        prompt = generate_prompt(**sample_data)

        # プロンプトに必要な要素が含まれているか確認
        required_elements = [
            "35.68",  # 緯度
            "139.65",  # 経度
            "420.50",  # CO2濃度
            "5.20",  # 偏差
            "2023-01-15",  # 日付
            "2.80",  # Zスコア
        ]

        missing = []
        for element in required_elements:
            if element not in prompt:
                missing.append(element)

        if missing:
            print(f"  FAILED: Missing elements in prompt: {missing}")
            return False

        # 文字数確認
        print(f"  Prompt length: {len(prompt)} characters")

        # 日本語が含まれているか確認
        if "CO2濃度" not in prompt or "推論" not in prompt:
            print("  FAILED: Prompt does not contain expected Japanese text")
            return False

        print("  PASSED: Prompt generated correctly with all required elements")
        print(f"\n  Generated prompt preview:")
        print("  " + "-" * 60)
        for line in prompt.split('\n')[:10]:  # 最初の10行のみ表示
            print(f"  {line}")
        print("  " + "-" * 60)

        return True

    except Exception as e:
        print(f"  FAILED: {e}")
        return False


def test_api_call_with_key():
    """Test 6 & 7: API呼び出しテスト"""
    print("\nTest 6 & 7: Testing API call...")

    api_key = os.environ.get('GEMINI_API_KEY')

    if not api_key:
        print("  SKIPPED: GEMINI_API_KEY not set in environment")
        print("  To run this test, set GEMINI_API_KEY environment variable")
        return None

    print(f"  API key found (length: {len(api_key)})")

    sample_data = {
        "lat": 35.6762,
        "lon": 139.6503,
        "co2": 420.5,
        "deviation": 5.2,
        "date": "2023-01-15",
        "severity": "high",
        "zscore": 2.8
    }

    try:
        print("  Generating prompt...")
        prompt = generate_prompt(**sample_data)

        print("  Calling Gemini API...")
        inference = call_gemini_api(prompt)

        print(f"  Response received ({len(inference)} characters)")

        # 200-300文字程度かチェック（日本語の場合）
        if 150 <= len(inference) <= 400:
            print(f"  PASSED: Response length is appropriate ({len(inference)} chars)")
        else:
            print(f"  WARNING: Response length is {len(inference)} chars (expected 200-300)")

        print("\n  Inference result:")
        print("  " + "-" * 60)
        print(f"  {inference}")
        print("  " + "-" * 60)

        return True

    except GeminiAPIError as e:
        print(f"  FAILED: API error: {e}")
        return False
    except Exception as e:
        print(f"  FAILED: Unexpected error: {e}")
        return False


def test_invalid_api_key():
    """Test 7 continued: 無効なAPIキーのエラーハンドリング"""
    print("\nTest 7: Testing invalid API key handling...")

    original_key = os.environ.get('GEMINI_API_KEY')

    # 無効なAPIキーを設定
    os.environ['GEMINI_API_KEY'] = 'invalid_key_12345'

    try:
        prompt = "Test prompt"
        call_gemini_api(prompt)
        print("  FAILED: Should have raised error for invalid API key")
        return False
    except GeminiAPIError as e:
        print(f"  PASSED: Invalid API key error handled: {e}")
        return True
    except Exception as e:
        print(f"  FAILED: Unexpected error type: {e}")
        return False
    finally:
        # 元の値を復元
        if original_key:
            os.environ['GEMINI_API_KEY'] = original_key
        else:
            os.environ.pop('GEMINI_API_KEY', None)


def main():
    """全テストを実行"""
    print("=" * 70)
    print("GEMINI_CLIENT.PY TEST SUITE")
    print("=" * 70)

    results = []

    # Test 4: API key error handling
    results.append(("Test 4: API key error", test_api_key_error()))

    # Test 5: Prompt generation
    results.append(("Test 5: Prompt generation", test_prompt_generation()))

    # Test 6 & 7: API call (if API key is available)
    api_result = test_api_call_with_key()
    if api_result is not None:
        results.append(("Test 6: API call", api_result))

        # Test 7: Invalid API key
        results.append(("Test 7: Invalid API key", test_invalid_api_key()))

    # サマリー表示
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result is True)
    failed = sum(1 for _, result in results if result is False)
    total = len(results)

    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"{test_name}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if failed > 0:
        print(f"\nWARNING: {failed} test(s) failed")
        sys.exit(1)
    else:
        print("\nAll tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
