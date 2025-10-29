import netCDF4 as nc
import numpy as np
import json
import os

# netCDFファイル群を解析し、上位10格子をGeoJSON形式で出力する

def analyze_and_convert_to_geojson(file_paths):
    # .nc4 のみを対象にする
    file_paths = [f for f in file_paths if f.endswith(".nc4")]
    
    if not file_paths:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "No valid .nc4 files found."})
        }

    results = []
    LL = 1.0  # 格子分割（1°×1°）
    LL = 1.0  # 格子分割（1°×1°）

    for tmp_file in file_paths:
        ds = nc.Dataset(tmp_file)

        lat = ds.variables['latitude'][:]
        lon = ds.variables['longitude'][:]
        xco2 = ds.variables['xco2'][:]

        # NaNを除去
        mask_valid = ~np.isnan(xco2)
        lat = lat[mask_valid]
        lon = lon[mask_valid]
        xco2 = xco2[mask_valid]

        if len(lat) == 0:
            continue

        # 格子境界
        lat_grid = np.arange(lat.min(), lat.max() + LL, LL)
        lon_grid = np.arange(lon.min(), lon.max() + LL, LL)

        # 各座標がどの格子に属するかをインデックス化
        lat_idx = np.digitize(lat, lat_grid) - 1
        lon_idx = np.digitize(lon, lon_grid) - 1

        # 範囲外のインデックスを除外
        valid_mask = (lat_idx >= 0) & (lat_idx < len(lat_grid)-1) & (lon_idx >= 0) & (lon_idx < len(lon_grid)-1)
        lat_idx = lat_idx[valid_mask]
        lon_idx = lon_idx[valid_mask]
        xco2_valid = xco2[valid_mask]

        # 格子ごとの合計とカウント (サイズを-1で修正)
        grid_sum = np.zeros((len(lat_grid)-1, len(lon_grid)-1))
        grid_count = np.zeros((len(lat_grid)-1, len(lon_grid)-1))

        np.add.at(grid_sum, (lat_idx, lon_idx), xco2_valid)
        np.add.at(grid_count, (lat_idx, lon_idx), 1)

        # 平均
        with np.errstate(divide='ignore', invalid='ignore'):
            grid_avg = grid_sum / grid_count
        grid_avg[grid_count == 0] = np.nan

        # 有効な格子のみを取得して上位10を抽出
        valid_values = grid_avg[~np.isnan(grid_avg)]
        if len(valid_values) == 0:
            continue

        # 有効な値のインデックスを取得
        valid_indices = np.where(~np.isnan(grid_avg))
        valid_i = valid_indices[0]
        valid_j = valid_indices[1]
        valid_values = grid_avg[valid_i, valid_j]

        # 上位10を選択
        top_n = min(10, len(valid_values))
        top_idx = np.argsort(valid_values)[::-1][:top_n]

        for k in range(top_n):
            idx = top_idx[k]
            i = valid_i[idx]
            j = valid_j[idx]
            avg_co2 = valid_values[idx]

            results.append({
                "lat_min": float(lat_grid[i]),
                "lat_max": float(lat_grid[i] + LL),
                "lon_min": float(lon_grid[j]),
                "lon_max": float(lon_grid[j] + LL),
                "avg_co2": float(avg_co2)
            })

    # 全ファイルからの上位10格子をさらに抽出
    global_top10 = sorted(results, key=lambda x: x['avg_co2'], reverse=True)[:10]

    # GeoJSON形式に変換
    features = []
    for g in global_top10:
        lat_c = (g['lat_min'] + g['lat_max']) / 2
        lon_c = (g['lon_min'] + g['lon_max']) / 2
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon_c, lat_c]},
            "properties": {
                "avg_co2": g['avg_co2'],
                "lat_min": g['lat_min'],
                "lat_max": g['lat_max'],
                "lon_min": g['lon_min'],
                "lon_max": g['lon_max']
            }
        })

    geojson = {"type": "FeatureCollection", "features": features}

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(geojson)
    }

def lambda_handler(event, context):
    """AWS Lambda handler function"""
    try:
        # デフォルトでtest.nc4ファイルを処理
        file_paths = ['/tmp/test.nc4']

        # Lambdaの場合、ファイルが存在しない可能性があるのでチェック
        existing_files = [f for f in file_paths if os.path.exists(f)]

        if not existing_files:
            # 現在のディレクトリでnc4ファイルを探す
            current_dir_files = [f for f in os.listdir('.') if f.endswith('.nc4')]
            if current_dir_files:
                existing_files = current_dir_files
            else:
                return {
                    "statusCode": 404,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"error": "No .nc4 files found"})
                }

        return analyze_and_convert_to_geojson(existing_files)

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)})
        }
