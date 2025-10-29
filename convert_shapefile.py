import geopandas as gpd
import json

def convert_and_simplify_countries():
    """Natural EarthのShapefileをGeoJSONに変換し、軽量化する"""

    # Shapefileを読み込み
    shapefile_path = "10m_cultural/10m_cultural/ne_10m_admin_0_countries.shp"
    print(f"Reading shapefile: {shapefile_path}")

    gdf = gpd.read_file(shapefile_path)
    print(f"Loaded {len(gdf)} countries")

    # 必要な列のみを選択（軽量化）
    columns_to_keep = ['NAME', 'NAME_EN', 'ISO_A2', 'ISO_A3', 'POP_EST', 'geometry']
    gdf_simplified = gdf[columns_to_keep].copy()

    # ジオメトリを簡略化（精度を下げてファイルサイズを縮小）
    print("Simplifying geometry...")
    gdf_simplified['geometry'] = gdf_simplified['geometry'].simplify(tolerance=0.01, preserve_topology=True)

    # GeoJSONに変換
    geojson_data = json.loads(gdf_simplified.to_json())

    # ファイルサイズを確認
    import sys
    size_mb = sys.getsizeof(json.dumps(geojson_data)) / 1024 / 1024
    print(f"GeoJSON size: {size_mb:.2f} MB")

    # GeoJSONファイルとして保存
    output_path = "countries.geojson"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(geojson_data, f, separators=(',', ':'))  # 余分な空白を削除

    print(f"Saved simplified GeoJSON to: {output_path}")

    # さらに軽量化したバージョン（最小限の国境のみ）
    print("Creating ultra-light version...")
    minimal_columns = ['NAME_EN', 'ISO_A3', 'geometry']
    gdf_minimal = gdf[minimal_columns].copy()

    # より強い簡略化
    gdf_minimal['geometry'] = gdf_minimal['geometry'].simplify(tolerance=0.05, preserve_topology=True)

    geojson_minimal = json.loads(gdf_minimal.to_json())

    output_path_minimal = "countries_minimal.geojson"
    with open(output_path_minimal, 'w', encoding='utf-8') as f:
        json.dump(geojson_minimal, f, separators=(',', ':'))

    minimal_size_mb = sys.getsizeof(json.dumps(geojson_minimal)) / 1024 / 1024
    print(f"Minimal GeoJSON size: {minimal_size_mb:.2f} MB")
    print(f"Saved minimal GeoJSON to: {output_path_minimal}")

    return output_path, output_path_minimal

if __name__ == "__main__":
    convert_and_simplify_countries()