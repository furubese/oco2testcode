import json

def parse_sample_json():
    """sample.jsonを読み込み、bodyのJSONをパースして整形したファイルを出力"""

    # sample.jsonを読み込む
    with open('sample.json', 'r', encoding='utf-8') as f:
        content = f.read()

    # JSON全体をパース
    data = json.loads(content)

    # bodyのJSON文字列を取得してパース
    if isinstance(data, dict) and 'body' in data:
        body_str = data['body']
        body_data = json.loads(body_str)
    elif isinstance(data, str):
        # dataが文字列の場合は直接パース
        body_data = json.loads(data)
    else:
        # すでにGeoJSON形式の場合
        body_data = data

    # 整形してparse_sample.jsonに出力
    with open('parse_sample.json', 'w', encoding='utf-8') as f:
        json.dump(body_data, f, indent=2, ensure_ascii=False)

    # 結果を表示
    print("OK sample.json was parsed successfully")
    print("OK parse_sample.json was created")
    print(f"Features count: {len(body_data.get('features', []))}")

    # 最初のfeatureの情報を表示
    if body_data.get('features'):
        first_feature = body_data['features'][0]
        coords = first_feature['geometry']['coordinates']
        co2 = first_feature['properties']['avg_co2']
        print(f"\nFirst data point:")
        print(f"  Coordinates: [{coords[0]:.2f}, {coords[1]:.2f}]")
        print(f"  CO2 concentration: {co2:.2f} ppm")

if __name__ == "__main__":
    parse_sample_json()
