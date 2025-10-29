"""
Flask API Server for CO2 Anomaly Reasoning
Provides endpoint for generating reasoning about CO2 concentration anomalies
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from typing import Dict, Any
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import our modules
import cache_manager
import gemini_client

app = Flask(__name__, static_folder='.')

# CORS設定: すべてのオリジン許可（開発用）
CORS(app)


# 静的ファイル配信ルート（APIより先に定義）
@app.route('/')
def index():
    """
    ルートページ - sample_calendar.htmlを配信
    """
    return send_from_directory('.', 'sample_calendar.html')


@app.route('/<path:filename>')
def serve_static(filename: str):
    """
    静的ファイル配信エンドポイント（GeoJSONなど）
    ただし /api/ で始まるパスは除外
    """
    # /api/ で始まる場合は404を返す（APIルートに任せる）
    if filename.startswith('api/') or filename.startswith('api'):
        return jsonify({"error": "Not found"}), 404

    # GeoJSONファイルはdata/geojson/から提供
    if filename.endswith('.geojson'):
        file_path = os.path.join('data', 'geojson', filename)
        if os.path.exists(file_path):
            return send_from_directory(os.path.join('data', 'geojson'), filename)

    # ファイルが存在するか確認
    file_path = os.path.join('.', filename)
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found", "path": filename}), 404

    return send_from_directory('.', filename)


@app.route('/api/health', methods=['GET'])
def health_check() -> tuple:
    """
    ヘルスチェックエンドポイント

    Returns:
        tuple: JSON response and status code
    """
    return jsonify({
        "status": "ok",
        "message": "Flask API Server is running",
        "endpoints": [
            {"method": "GET", "path": "/", "description": "Serve sample_calendar.html"},
            {"method": "GET", "path": "/api/health", "description": "Health check"},
            {"method": "POST", "path": "/api/reasoning", "description": "Generate CO2 anomaly reasoning"}
        ]
    }), 200


@app.route('/api/reasoning', methods=['POST'])
def reasoning() -> tuple:
    """
    CO2異常データに対する推論生成エンドポイント

    Request Body (JSON):
        - lat (float): 緯度
        - lon (float): 経度
        - co2 (float): CO2濃度 (ppm)
        - deviation (float): 偏差 (ppm)
        - date (str): 日付 (YYYY-MM-DD)
        - severity (str): 異常度 ("high", "medium", "low")
        - zscore (float): Zスコア

    Returns:
        tuple: JSON response and status code

    Response Format:
        {
            "reasoning": str,
            "cached": bool,
            "cache_key": str
        }
    """
    try:
        # 1. リクエストパース
        data = request.get_json()

        # 必須パラメータのバリデーション
        required_fields = ['lat', 'lon', 'co2', 'deviation', 'date', 'severity', 'zscore']
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            return jsonify({
                "error": "Missing required fields",
                "missing_fields": missing_fields
            }), 400

        # パラメータの取得
        lat = float(data['lat'])
        lon = float(data['lon'])
        co2 = float(data['co2'])
        deviation = float(data['deviation'])
        date = str(data['date'])
        severity = str(data['severity'])
        zscore = float(data['zscore'])

        # severityのバリデーション
        if severity not in ['high', 'medium', 'low']:
            return jsonify({
                "error": "Invalid severity value",
                "message": "severity must be one of: high, medium, low"
            }), 400

        # 2. キャッシュキー生成
        cache_key = cache_manager.generate_cache_key(lat, lon, date)

        # 3. キャッシュ確認
        cached_reasoning = cache_manager.get_cached_reasoning(cache_key)

        # 4. キャッシュヒット → 即座に返却
        if cached_reasoning:
            return jsonify({
                "reasoning": cached_reasoning,
                "cached": True,
                "cache_key": cache_key
            }), 200

        # 5. キャッシュミス → Gemini API呼び出し
        try:
            reasoning_text = gemini_client.generate_inference(
                lat=lat,
                lon=lon,
                co2=co2,
                deviation=deviation,
                date=date,
                severity=severity,
                zscore=zscore
            )
        except gemini_client.GeminiAPIError as e:
            return jsonify({
                "error": "Gemini API error",
                "message": str(e)
            }), 500

        # 6. キャッシュ保存
        metadata = {
            "lat": lat,
            "lon": lon,
            "co2": co2,
            "deviation": deviation,
            "severity": severity,
            "zscore": zscore
        }

        save_success = cache_manager.save_to_cache(cache_key, reasoning_text, metadata)

        if not save_success:
            # キャッシュ保存に失敗してもレスポンスは返す
            print(f"Warning: Failed to save to cache for key: {cache_key}")

        # 7. レスポンス返却
        return jsonify({
            "reasoning": reasoning_text,
            "cached": False,
            "cache_key": cache_key
        }), 200

    except ValueError as e:
        return jsonify({
            "error": "Invalid parameter type",
            "message": str(e)
        }), 400

    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


@app.errorhandler(405)
def method_not_allowed(error) -> tuple:
    """
    405エラーハンドラー
    """
    return jsonify({
        "error": "Method not allowed",
        "message": "The HTTP method is not supported for this endpoint"
    }), 405


if __name__ == '__main__':
    print("Starting Flask API Server...")
    print("Server will run on http://localhost:5000")
    print("Press CTRL+C to quit")

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
