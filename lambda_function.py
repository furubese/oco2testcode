import json
import download_s3
import analyze_geojson

def lambda_handler(event, context):

    # ファイルを /tmp にダウンロード
    download_result = download_s3.lambda_handler(event, context)
    downloaded_files = download_result.get("downloaded_files", [])

    if not downloaded_files:
        return {
            "statusCode": 404,
            "body": json.dumps({"error": "No files downloaded"})
        }

    # ダウンロードしたファイルを解析して GeoJSON 生成
    geojson_result = analyze_geojson.analyze_and_convert_to_geojson(downloaded_files)

    # 解析結果を返す
    return geojson_result
