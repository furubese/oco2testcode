import netCDF4 as nc
import numpy as np
import itertools

# netCDF ファイルを読み込み
ds = nc.Dataset("test.nc4")

# 緯度
lat = ds.variables['latitude'][:]
# 経度
lon = ds.variables['longitude'][:]
# 平均Co2濃度
xco2 = ds.variables['xco2'][:]

# 格子分割レベル（1°×1°）
LL = 1.0

# 格子分割
lat_grid = np.arange(lat.min(), lat.max(), LL)
lon_grid = np.arange(lon.min(), lon.max(), LL)

# generator関数で格子平均を逐次生成
def gen_grid_averages():
    for lat_min, lon_min in itertools.product(lat_grid, lon_grid):
 
        lat_max = lat_min + LL
        lon_max = lon_min + LL
        lat_mask = (lat >= lat_min) & (lat < lat_max)
        lon_mask = (lon >= lon_min) & (lon < lon_max)
        # 格子範囲でマスク（取得）
        mask = lat_mask & lon_mask
        subset = xco2[mask]
        if subset.size == 0:
            continue

        # gen_gridを返答
        yield {'lat_min': lat_min, 'lat_max': lat_max,
               'lon_min': lon_min, 'lon_max': lon_max,
               'avg_co2': np.nanmean(subset)}

# generator を使って全格子平均を計算し、上位10格子を抽出
top10 = sorted(gen_grid_averages(), key=lambda x: x['avg_co2'], reverse=True)[:10]

# 5. 結果表示
for i, g in enumerate(top10, 1):
    print(f"{i}: Lat {g['lat_min']}-{g['lat_max']}°, "
          f"Lon {g['lon_min']}-{g['lon_max']}° -> {g['avg_co2']:.2f} ppm")
