# CO₂異常値可視化マップ - Phase 1 (ローカルプロトタイプ)

AI搭載のCO₂濃度異常値分析システムです。OCO-2衛星データから検出されたCO₂異常値を地図上に可視化し、Google Gemini APIを利用して異常値の原因を推論します。

## プロジェクト概要

このプロジェクトは、地球観測衛星OCO-2から収集されたCO₂濃度データの異常値を可視化し、AI（Google Gemini）を使って異常値の原因を分析するWebアプリケーションです。

**主な機能:**
- 時系列でCO₂異常値データを表示（2020年12月、2021年3月、2023年1-10月）
- インタラクティブな地図インターフェース（Leaflet.js）
- マーカークリックによる詳細情報表示（サイドパネル）
- Gemini APIによる原因推論（産業活動、交通、気象、地理的要因など）
- JSONキャッシュによるAPI呼び出し最適化（SHA256ハッシュベース）
- Flask統合サーバー（静的ファイル配信 + REST API）

**Phase 1の目的:**
- ローカル環境でのプロトタイプ開発
- Flask + Gemini APIによる原因推論機能の実装
- Phase 2（AWS Lambda + DynamoDB移行）への基盤構築

## 必要な環境

- **Python**: 3.8以上
- **ブラウザ**: Chrome、Firefox、Edge、Safari（最新版推奨）
- **インターネット接続**: Gemini API呼び出し、地図タイル読み込みに必要
- **Gemini APIキー**: Google AI Studioから取得（無料）

## Gemini APIキーの取得方法

1. **Google AI Studioにアクセス**
   - URL: https://makersuite.google.com/app/apikey
   - または: https://aistudio.google.com/app/apikey

2. **Googleアカウントでログイン**
   - Googleアカウントが必要です（Gmailアドレス）

3. **APIキーを作成**
   - 「Create API Key」ボタンをクリック
   - 既存のGoogle Cloud Projectを選択、または新規作成
   - APIキーが生成されます（例: `AIzaSyA...`）

4. **APIキーをコピー**
   - 生成されたAPIキーをコピーして保存してください
   - このキーは`.env`ファイルで使用します

**注意事項:**
- Gemini API無料プランの制限: 1日あたり60リクエスト
- APIキーは絶対に公開しないでください（`.env`ファイルは`.gitignore`に追加済み）

## セットアップ手順

### 1. プロジェクトのダウンロード

```bash
# Gitリポジトリをクローン
git clone <repository_url>
cd <project_directory>
```

または、ZIPファイルをダウンロードして解凍してください。

### 2. Python依存関係のインストール

```bash
# requirements.txtから依存関係をインストール
pip install -r requirements.txt
```

**インストールされるパッケージ:**
- `flask` (Webサーバーフレームワーク)
- `flask-cors` (クロスオリジンリクエスト対応)
- `google-generativeai` (Gemini API クライアント)

### 3. 環境変数ファイルの作成

`.env.example`をコピーして`.env`ファイルを作成します:

```bash
# Windowsの場合
copy .env.example .env

# Mac/Linuxの場合
cp .env.example .env
```

`.env`ファイルを編集して、取得したGemini APIキーを設定します:

```env
# Gemini API Configuration
# Get your API key from: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your_api_key_here  # ここにAPIキーを貼り付け

# Flask Server Configuration
# Port number for the Flask API server (default: 5000)
FLASK_PORT=5000
```

**注意:** 現在、`app.py` は `.env` の `FLASK_PORT` を使用せず、ハードコードされた5000番ポートを使用します。ポートを変更したい場合は `app.py:215` の `port=5000` を直接編集してください。

### 4. Flaskサーバーの起動

```bash
python app.py
```

以下のようなメッセージが表示されれば成功です:

```
 * Serving Flask app 'app'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment.
 * Running on http://127.0.0.1:5000
```

**注意:** サーバーを起動したまま次のステップに進んでください。

### 5. ブラウザでアプリケーションを開く

1. ブラウザを開く
2. アドレスバーに `http://localhost:5000` を入力
3. Flaskサーバーが自動的に `sample_calendar.html` を配信します

**注意:** Flaskサーバーは静的ファイルとAPIの両方を提供します。ブラウザから直接HTMLファイルを開くのではなく、必ず `http://localhost:5000` を通じてアクセスしてください。

## 使い方

### 基本操作

1. **アプリケーションへのアクセス**
   - ブラウザで `http://localhost:5000` にアクセス
   - Flaskサーバーが自動的に `sample_calendar.html` を配信します

2. **年月の選択**
   - 画面左上のドロップダウンメニューから年（2020～2025）と月（1～12月）を選択
   - 利用可能なデータ: 2020年12月、2021年3月、2023年1-10月
   - データが自動的に読み込まれ、地図上にマーカーが表示されます

3. **地図の操作**
   - **ドラッグ**: 地図を移動
   - **スクロール/ピンチ**: ズームイン/ズームアウト
   - **マーカーホバー**: マーカーが拡大表示

4. **マーカーのクリック**
   - マーカーをクリックすると、右側にサイドパネルが開きます
   - **ローディング表示**: Gemini APIが推論を実行中（数秒間）
   - **推論結果表示**: AI が分析した原因が表示されます

5. **サイドパネルの情報**
   - **CO₂濃度**: 測定値（ppm）とレベル評価
   - **位置情報**: 緯度・経度・観測日
   - **測定データ**: 基準値、偏差、Z-Score
   - **異常検出情報**: 異常度、検出日数
   - **AI原因推論**: Geminiによる詳細分析

### キャッシュ機能

- **初回クリック**: Gemini APIを呼び出し、推論を実行（2～5秒）
- **2回目以降**: JSONキャッシュ（`cache.json`）から即座に結果を取得
- **キャッシュの利点**:
  - API呼び出し回数を削減（無料枠の節約）
  - レスポンス時間の短縮
  - オフライン時の結果閲覧

**キャッシュファイルの場所:**
```
cache.json  # プロジェクトルートに自動生成
```

## トラブルシューティング

### 1. Flaskサーバーが起動しない

**症状:** `python app.py` でエラーが発生

**原因と対処法:**
- **依存関係未インストール**
  ```bash
  pip install -r requirements.txt
  ```
- **ポート5000が使用中**
  - `.env`ファイルで別のポートを指定:
    ```env
    FLASK_PORT=5001
    ```
- **Pythonバージョンが古い**
  ```bash
  python --version  # 3.8以上か確認
  ```

### 2. API推論が失敗する

**症状:** サイドパネルに「AI推論サービスに接続できませんでした」と表示

**原因と対処法:**
- **Flaskサーバーが起動していない**
  - `python app.py` でサーバーを起動してください
- **APIキーが未設定または間違っている**
  - `.env`ファイルを確認:
    ```env
    GEMINI_API_KEY=AIzaSy...  # 正しいキーか確認
    ```
- **APIキーの無料枠を超過**
  - 1日60リクエストの制限を超えた場合、翌日まで待つか、有料プランにアップグレード
- **インターネット接続の問題**
  - ネットワーク接続を確認してください

### 3. 地図が表示されない

**症状:** 画面が真っ白、または地図タイルが表示されない

**原因と対処法:**
- **Leaflet.jsの読み込み失敗**
  - インターネット接続を確認
  - ブラウザのコンソールでエラーを確認（F12キー → Console）
- **ブラウザのキャッシュ問題**
  ```
  Ctrl + Shift + R (Windows)
  Cmd + Shift + R (Mac)
  ```
  でページを強制リロード

### 4. データが表示されない

**症状:** 年月を選択してもマーカーが表示されない

**原因と対処法:**
- **GeoJSONファイルが存在しない**
  - `data/geojson/` ディレクトリに `anomalies202306.geojson` などのファイルがあるか確認
  - 利用可能なデータ: 2020年12月、2021年3月、2023年1-10月のみ
- **Flaskサーバーが起動していない**
  - `python app.py` でサーバーを起動してください
  - `http://localhost:5000` でアクセスできることを確認
- **ファイル名の不一致**
  - 例: 2023年6月のデータは `data/geojson/anomalies202306.geojson`
- **ブラウザコンソールでエラー確認**
  - F12キー → Console タブ → エラーメッセージを確認

### 5. CORS エラー

**症状:** ブラウザコンソールに「CORS policy」エラー

**原因と対処法:**
- **HTMLファイルを直接ブラウザで開いている**
  - ✗ 間違い: `file:///C:/Users/.../sample_calendar.html`
  - ✓ 正解: `http://localhost:5000` でアクセス
  - Flaskサーバーを経由してアクセスする必要があります
- **Flaskサーバーが起動していない**
  - `python app.py` でサーバーを起動
- **CORSが正しく設定されていない**
  - `app.py:22`で `flask-cors` が正しく設定されているか確認:
    ```python
    from flask_cors import CORS
    CORS(app)
    ```

### よくある質問（FAQ）

**Q: APIキーは無料ですか？**
A: はい、Gemini APIには無料プランがあります（1日60リクエストまで）。

**Q: cache.jsonファイルは削除しても大丈夫ですか？**
A: はい。削除すると全てのキャッシュがクリアされ、次回クリック時に再度API呼び出しが行われます。

**Q: オフラインでも使えますか？**
A: 一度キャッシュされたデータはオフラインでも閲覧可能です。ただし、新しいマーカーのクリックにはインターネット接続が必要です。

**Q: 複数の地点を同時に分析できますか？**
A: はい。複数のマーカーを順番にクリックして分析できます。キャッシュにより2回目以降は高速です。

**Q: なぜブラウザから直接HTMLファイルを開けないのですか？**
A: このアプリはFlaskサーバーを通じてGeoJSONファイルとAPI推論を提供します。`file://` プロトコルではCORSエラーが発生するため、必ず `http://localhost:5000` でアクセスしてください。

**Q: 利用可能なデータの期間は？**
A: 現在、2020年12月、2021年3月、2023年1-10月のデータが利用可能です。他の期間のデータは `data/geojson/` ディレクトリに追加することで利用できます。

## Phase 2への移行準備

このプロトタイプは、将来的にAWSへの移行を想定して設計されています。

### 現在のアーキテクチャ（Phase 1）

```
ブラウザ (sample_calendar.html)
    ↓ HTTP POST
Flask (app.py) ← Python 3.8+
    ↓
cache_manager.py → cache.json (ローカルファイル)
    ↓
gemini_client.py → Gemini API (Google)
```

### Phase 2の目標アーキテクチャ

```
ブラウザ (S3静的ホスティング)
    ↓ HTTPS
API Gateway
    ↓
Lambda関数 (app.py を変換)
    ↓
DynamoDB (cache.json を移行)
    ↓
Gemini API (Google)
```

### 移行時の主な変更点

| コンポーネント | Phase 1 | Phase 2 |
|------------|---------|---------|
| **フロントエンド** | ローカルHTMLファイル | S3 静的ホスティング |
| **バックエンド** | Flask (app.py) | AWS Lambda |
| **キャッシュ** | cache.json | DynamoDB |
| **エンドポイント** | http://localhost:5000 | API Gateway URL |
| **環境変数** | .env ファイル | Lambda 環境変数 |
| **認証** | なし | API Key / IAM |

### データ構造の互換性

Phase 1のJSONキャッシュはDynamoDBと互換性があります:

**cache.json (Phase 1):**
```json
{
  "35.6895_139.6917_202306": {
    "reasoning": "この地点では...",
    "created_at": 1234567890,
    "metadata": {
      "lat": 35.6895,
      "lon": 139.6917,
      "co2": 418.45
    }
  }
}
```

**DynamoDB (Phase 2):**
- **Partition Key**: `cache_key` (String): `"35.6895_139.6917_202306"`
- **Attributes**:
  - `reasoning` (String)
  - `created_at` (Number)
  - `metadata` (Map)
- **TTL**: 90日間（オプション）

### 移行手順の概要

1. **S3バケット作成**: 静的ウェブサイトホスティングを有効化
2. **DynamoDBテーブル作成**: `cache_key`をパーティションキーに設定
3. **Lambda関数作成**: `app.py`を変換
   - `cache_manager.py` → DynamoDB SDKを使用
   - `gemini_client.py` → そのまま使用可能
4. **API Gateway設定**: Lambda関数を統合
5. **環境変数設定**: Lambda環境変数にAPIキーを設定
6. **CORS設定**: API GatewayでCORSを有効化
7. **フロントエンド更新**: `sample_calendar.html`のエンドポイントURLを変更

## ファイル構成

```
project/
├── app.py                    # Flaskメインサーバー（静的ファイル配信 + API）
├── cache_manager.py          # JSONキャッシュ管理
├── gemini_client.py          # Gemini API呼び出し
├── requirements.txt          # Python依存関係
├── package.json              # Node.js依存関係（Playwrightテスト用）
├── .env                      # 環境変数（要作成、gitignore対象）
├── .env.example              # 環境変数テンプレート
├── .gitignore                # Git除外設定
├── Dockerfile                # Dockerコンテナ設定
├── cache.json                # キャッシュデータ（自動生成、gitignore対象）
├── sample_calendar.html      # メインアプリケーション
├── README.md                 # このファイル
├── TEST_RESULTS.md           # エンドツーエンドテスト結果
├── data/
│   ├── geojson/              # GeoJSONデータファイル
│   │   ├── anomalies202012.geojson   # 2020年12月
│   │   ├── anomalies202103.geojson   # 2021年3月
│   │   ├── anomalies202301.geojson   # 2023年1月
│   │   ├── anomalies202302-202310.geojson # 2023年2-10月
│   │   ├── countries.geojson         # 国境データ
│   │   └── countries_minimal.geojson # 簡略版国境データ
│   ├── nc4/                  # NetCDF4形式の生データ
│   └── 10m_cultural/         # Natural Earthの地理データ
├── tests/                    # テストファイル
│   ├── e2e_test.py           # エンドツーエンドテスト
│   ├── test_api_errors.py
│   ├── test_cache_manager.py
│   ├── test_gemini_client.py
│   └── ...
├── docs/                     # ドキュメント
├── scripts/                  # ユーティリティスクリプト
└── node_modules/             # Node.js依存関係（自動生成）
```

## 技術スタック

### フロントエンド
- **HTML5/CSS3**: レスポンシブUI
- **JavaScript (ES6+)**: 非同期処理、Fetch API
- **Leaflet.js 1.9.4**: インタラクティブ地図

### バックエンド
- **Python 3.8+**
- **Flask 3.0+**: Webフレームワーク（静的ファイル配信 + REST API）
- **Flask-CORS 4.0+**: クロスオリジンリクエスト対応
- **Google Generative AI 0.3+**: Gemini API クライアント
- **python-dotenv 1.0+**: 環境変数管理

### テスト
- **Playwright 1.56+**: ブラウザE2Eテスト（Node.js）
- **pytest**: Pythonユニットテスト

### データ形式
- **GeoJSON**: 地理空間データ（CO₂異常値、国境線）
- **JSON**: キャッシュデータ（API推論結果）
- **NetCDF4**: 衛星観測データ（生データ、処理前）

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## クレジット

- **CO₂データソース**: OCO-2衛星観測データ（NASA）
- **AI推論**: Google Gemini API
- **地図タイル**: OpenStreetMap contributors
- **地図ライブラリ**: Leaflet.js

## サポート

問題が発生した場合は、以下を確認してください:

1. このREADMEの「トラブルシューティング」セクション
2. ブラウザのコンソール（F12キー → Console）でエラーメッセージを確認
3. Flaskサーバーのターミナル出力を確認

## 開発者向け情報

### テストの実行

```bash
# キャッシュマネージャーのテスト
python test_cache_manager.py

# Gemini APIクライアントのテスト
python test_gemini_client.py

# サイドパネル機能のテスト
python test_sidepanel.py

# 完了条件のテスト
python test_completion_criteria.py
```

### デバッグモード

`app.py:214-218`でFlaskのデバッグモードが有効になっています:
```python
if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
```

デバッグモードの特徴:
- コードの変更が自動的に反映されます
- エラー発生時に詳細なスタックトレースが表示されます
- 本番環境では必ず `debug=False` に設定してください

### APIエンドポイント

**GET /** - メインアプリケーション配信
- `sample_calendar.html` を配信

**GET /<path:filename>** - 静的ファイル配信
- GeoJSONファイル: `data/geojson/` から提供
- その他の静的ファイル: プロジェクトルートから提供

**GET /api/health** - ヘルスチェック
```json
{
  "status": "ok",
  "message": "Flask API Server is running",
  "endpoints": [...]
}
```

**POST /api/reasoning** - AI推論エンドポイント

リクエスト:
```json
{
  "lat": 35.6895,
  "lon": 139.6917,
  "co2": 418.45,
  "deviation": 6.45,
  "date": "oco2_LtCO2_200901_B10206Ar.nc4",
  "severity": "high",
  "zscore": 3.2
}
```

レスポンス:
```json
{
  "reasoning": "この地点では東京都心部に位置しており...",
  "cached": false,
  "cache_key": "sha256_hash_value"
}
```

---

**Phase 1 プロトタイプ完成日**: 2025年10月

**次のステップ**: Phase 2（AWS Lambda + DynamoDB移行）の計画策定
