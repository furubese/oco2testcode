"""
Gemini API クライアント
CO2異常検知データに対する推論を生成するためのGemini API呼び出しモジュール
"""

import os
import google.generativeai as genai
from typing import Optional


class GeminiAPIError(Exception):
    """Gemini API関連のエラー"""
    pass


def load_api_key() -> str:
    """
    環境変数からGemini APIキーを読み込む

    Returns:
        str: APIキー

    Raises:
        GeminiAPIError: APIキーが設定されていない場合
    """
    api_key = os.environ.get('GEMINI_API_KEY')

    if not api_key:
        raise GeminiAPIError(
            "GEMINI_API_KEY environment variable is not set. "
            "Please set it with your Gemini API key."
        )

    return api_key


def generate_prompt(
    lat: float,
    lon: float,
    co2: float,
    deviation: float,
    date: str,
    severity: str,
    zscore: float
) -> str:
    """
    CO2異常データから推論用のプロンプトを生成

    Args:
        lat: 緯度
        lon: 経度
        co2: CO2濃度 (ppm)
        deviation: 偏差 (ppm)
        date: 日付 (YYYY-MM-DD形式)
        severity: 異常度 ("high", "medium", "low")
        zscore: Zスコア

    Returns:
        str: Gemini APIに送信するプロンプト
    """
    severity_ja = {
        "high": "高",
        "medium": "中",
        "low": "低"
    }.get(severity, severity)

    prompt = f"""以下のCO2濃度異常データについて、専門家の視点から分析し、日本語で200-300文字程度で推論してください。

【観測データ】
- 日付: {date}
- 位置: 緯度 {lat:.2f}°, 経度 {lon:.2f}°
- CO2濃度: {co2:.2f} ppm
- 偏差: {deviation:.2f} ppm
- 異常度: {severity_ja}
- Zスコア: {zscore:.2f}

【推論内容】
この地点でのCO2濃度異常の考えられる原因、その地域の特徴、および環境への影響について、科学的根拠に基づいて分析してください。
地理的な特性や、その時期の気候的要因も考慮してください。
"""

    return prompt


def call_gemini_api(prompt: str, model_name: str = "gemini-1.5-flash") -> str:
    """
    Gemini APIを呼び出して推論を取得
    APIキーが設定されていない場合はサンプルメッセージを返す

    Args:
        prompt: 送信するプロンプト
        model_name: 使用するGeminiモデル名（デフォルト: gemini-1.5-flash）

    Returns:
        str: Geminiからの推論結果、またはサンプルメッセージ
    """
    # APIキーが設定されているかチェック
    api_key = os.environ.get('GEMINI_API_KEY')

    if not api_key:
        # APIキー未設定時はサンプルメッセージを返す
        return "API Keyが設定されていません。"

    try:
        # APIキーを設定
        genai.configure(api_key=api_key)

        # モデルを初期化
        model = genai.GenerativeModel(model_name)

        # プロンプトを送信
        response = model.generate_content(prompt)

        # レスポンスチェック
        if not response or not response.text:
            raise GeminiAPIError("Empty response received from Gemini API")

        return response.text.strip()

    except Exception as e:
        if isinstance(e, GeminiAPIError):
            raise
        else:
            raise GeminiAPIError(f"Failed to call Gemini API: {str(e)}") from e


def generate_inference(
    lat: float,
    lon: float,
    co2: float,
    deviation: float,
    date: str,
    severity: str,
    zscore: float,
    model_name: str = "gemini-1.5-flash"
) -> str:
    """
    CO2異常データから推論を生成する便利関数

    Args:
        lat: 緯度
        lon: 経度
        co2: CO2濃度 (ppm)
        deviation: 偏差 (ppm)
        date: 日付 (YYYY-MM-DD形式)
        severity: 異常度 ("high", "medium", "low")
        zscore: Zスコア
        model_name: 使用するGeminiモデル名

    Returns:
        str: Geminiからの推論結果

    Raises:
        GeminiAPIError: API呼び出しに失敗した場合
    """
    prompt = generate_prompt(lat, lon, co2, deviation, date, severity, zscore)
    return call_gemini_api(prompt, model_name)


if __name__ == "__main__":
    # テスト実行
    print("=== Gemini Client Test ===\n")

    # サンプルデータ
    test_data = {
        "lat": 35.6762,
        "lon": 139.6503,
        "co2": 420.5,
        "deviation": 5.2,
        "date": "2023-01-15",
        "severity": "high",
        "zscore": 2.8
    }

    try:
        print("1. Testing load_api_key()...")
        api_key = load_api_key()
        print(f"   ✓ API key loaded (length: {len(api_key)})\n")

        print("2. Testing generate_prompt()...")
        prompt = generate_prompt(**test_data)
        print(f"   ✓ Prompt generated ({len(prompt)} characters)\n")
        print("Generated prompt:")
        print("-" * 50)
        print(prompt)
        print("-" * 50 + "\n")

        print("3. Testing call_gemini_api()...")
        inference = call_gemini_api(prompt)
        print(f"   ✓ Inference received ({len(inference)} characters)\n")
        print("Inference result:")
        print("-" * 50)
        print(inference)
        print("-" * 50 + "\n")

        print("✓ All tests passed!")

    except GeminiAPIError as e:
        print(f"   ✗ Error: {e}\n")
        print("Note: Set GEMINI_API_KEY environment variable to run full tests")
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")
