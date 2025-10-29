"""
gemini_client.py の使用例デモ
"""

import os
from gemini_client import generate_inference, call_gemini_api, generate_prompt


def demo():
    print("=" * 70)
    print("Gemini Client Demo")
    print("=" * 70)

    # サンプルデータ
    sample_data = {
        "lat": 35.6762,
        "lon": 139.6503,
        "co2": 420.5,
        "deviation": 5.2,
        "date": "2023-01-15",
        "severity": "high",
        "zscore": 2.8
    }

    print("\nSample CO2 Anomaly Data:")
    print(f"  Latitude: {sample_data['lat']}")
    print(f"  Longitude: {sample_data['lon']}")
    print(f"  CO2 Concentration: {sample_data['co2']} ppm")
    print(f"  Deviation: {sample_data['deviation']} ppm")
    print(f"  Date: {sample_data['date']}")
    print(f"  Severity: {sample_data['severity']}")
    print(f"  Z-Score: {sample_data['zscore']}")

    # APIキーの状態を確認
    api_key = os.environ.get('GEMINI_API_KEY')

    print("\n" + "-" * 70)
    print("API Key Status:")
    if api_key:
        print(f"  [SET] API key is configured (length: {len(api_key)})")
        print("  Will call actual Gemini API")
    else:
        print("  [NOT SET] API key is not configured")
        print("  Will return sample message")

    # 推論を生成
    print("\n" + "-" * 70)
    print("Generating inference...")
    print("-" * 70)

    try:
        inference = generate_inference(**sample_data)

        print("\nInference Result:")
        print("-" * 70)
        print(inference)
        print("-" * 70)
        print(f"\nResult length: {len(inference)} characters")

    except Exception as e:
        print(f"\nError: {e}")

    print("\n" + "=" * 70)
    print("Demo completed")
    print("=" * 70)


if __name__ == "__main__":
    demo()
