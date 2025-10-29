"""
APIキー未設定時の動作確認テスト
"""

import os
import sys

# APIキーを削除
if 'GEMINI_API_KEY' in os.environ:
    del os.environ['GEMINI_API_KEY']

from gemini_client import call_gemini_api, generate_inference


def test_call_gemini_api_no_key():
    """call_gemini_api関数のテスト"""
    print("Test 1: call_gemini_api without API key")

    result = call_gemini_api("Test prompt")

    expected = "API Keyが設定されていません。"

    if result == expected:
        print(f"  [PASSED] Returned expected message")
        print(f"  Message: {result}")
        return True
    else:
        print(f"  [FAILED] Unexpected result")
        print(f"  Expected: {expected}")
        print(f"  Got: {result}")
        return False


def test_generate_inference_no_key():
    """generate_inference関数のテスト"""
    print("\nTest 2: generate_inference without API key")

    sample_data = {
        "lat": 35.6762,
        "lon": 139.6503,
        "co2": 420.5,
        "deviation": 5.2,
        "date": "2023-01-15",
        "severity": "high",
        "zscore": 2.8
    }

    result = generate_inference(**sample_data)

    expected = "API Keyが設定されていません。"

    if result == expected:
        print(f"  [PASSED] Returned expected message")
        print(f"  Message: {result}")
        return True
    else:
        print(f"  [FAILED] Unexpected result")
        print(f"  Expected: {expected}")
        print(f"  Got: {result}")
        return False


def main():
    print("=" * 70)
    print("API Key Not Set Behavior Test")
    print("=" * 70)

    results = []

    results.append(("call_gemini_api", test_call_gemini_api_no_key()))
    results.append(("generate_inference", test_generate_inference_no_key()))

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "[PASSED]" if result else "[FAILED]"
        print(f"{test_name}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n[SUCCESS] All tests passed!")
        print("API key not set behavior is working correctly.")
        sys.exit(0)
    else:
        print("\n[FAILURE] Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
