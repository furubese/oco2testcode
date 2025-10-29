import json

# Read anomalies.geojson
with open('anomalies.geojson', 'r', encoding='utf-8') as f:
    geojson_data = json.load(f)

# Read sample_simple.html template
with open('sample_simple.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

# Replace the loadSampleData function with embedded data
embedded_data_script = f'''    // 埋め込みデータ
    const embeddedData = {json.dumps(geojson_data, ensure_ascii=False, indent=2)};

    // データを読み込んで表示
    function loadSampleData() {{
      try {{
        updateStatus('CO₂異常値データを読み込み中...');
        console.log('Loaded CO2 anomaly data:', embeddedData.features.length, 'points');
        addCO2DataToMap(embeddedData);
        updateStatus('CO₂異常値データ表示完了 (' + embeddedData.features.length + '地点)');
      }} catch (error) {{
        console.error('Failed to load data:', error);
        updateStatus('データ読み込みエラー: ' + error.message);
      }}
    }}'''

# Replace the fetch-based loadSampleData with embedded version
old_function = '''    // anomalies.geojsonからデータを読み込んで表示
    async function loadSampleData() {
      try {
        updateStatus('CO₂異常値データを読み込み中...');

        // キャッシュバスター: タイムスタンプをクエリパラメータに追加
        const timestamp = new Date().getTime();
        const response = await fetch('anomalies.geojson?t=' + timestamp);
        if (!response.ok) {
          throw new Error('Failed to load anomalies.geojson: ' + response.status);
        }

        const sampleData = await response.json();
        console.log('Loaded CO2 anomaly data:', sampleData.features.length, 'points');

        addCO2DataToMap(sampleData);
        updateStatus('CO₂異常値データ表示完了 (' + sampleData.features.length + '地点)');

      } catch (error) {
        console.error('Failed to load data:', error);
        updateStatus('データ読み込みエラー: ' + error.message);
      }
    }'''

static_html = html_content.replace(old_function, embedded_data_script)

# Update title to indicate this is the static version
static_html = static_html.replace(
    '<title>CO₂ 濃度可視化マップ</title>',
    '<title>CO₂ 濃度可視化マップ (Static)</title>'
)

# Write to sample_static.html
with open('sample_static.html', 'w', encoding='utf-8') as f:
    f.write(static_html)

print('Created sample_static.html successfully!')
print(f'Embedded {len(geojson_data["features"])} features')
