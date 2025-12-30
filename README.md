# Job Matching Flow with LangChain

This project reproduces the job matching workflows from a Dify application using LangChain and related libraries.

## Workflows Implemented

1. **format_yoin**: Structure personnel data from emails
2. **format_anken**: Structure job/project data from emails  
3. **index_yoin**: Register personnel data to RAG (Pinecone)
4. **matching_yoin**: Match personnel to job requirements

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set environment variables in `.env`:
   - OPENAI_API_KEY
   - PINECONE_API_KEY  
   - PINECONE_INDEX_HOST

## Usage

Run the script with the desired action:

```bash
python job_matching_flow.py <action> [parameters...]
```

### Actions

- **format_yoin**: Structure personnel data
  ```bash
  python job_matching_flow.py format_yoin start_date=2024-01-01 end_date=2024-12-31 limit=100
  ```

- **format_anken**: Structure job data
  ```bash
  python job_matching_flow.py format_anken start_date=2024-01-01 end_date=2024-12-31 limit=100
  ```

- **index_yoin**: Index personnel data to vector DB
  ```bash
  python job_matching_flow.py index_yoin start_date=2024-01-01 end_date=2024-12-31 limit=100
  ```

- **matching_yoin**: Match personnel to job
  ```bash
  python job_matching_flow.py matching_yoin query="Python developer needed" anken='{"案件名":"Python開発","必須スキル":"Python,Django","作業場所":"東京","単価":"50万円","備考":""}'
  ```

## Dependencies

- langchain
- langchain-openai
- langchain-pinecone
- requests
- pydantic
- python-dotenv
- fastapi
- uvicorn

## API Usage

The application can also be run as a FastAPI server for external access.

### Starting the API Server

```bash
# Development mode
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### API Endpoints

- **POST /format_yoin**: Structure personnel data
- **POST /format_anken**: Structure job data
- **POST /index_yoin**: Index personnel data to vector DB
- **POST /matching_yoin**: Match personnel to job
- **GET /health**: Health check

### API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Example API Calls

```bash
# Format personnel data
curl -X POST "http://localhost:8000/format_yoin" \
  -H "Content-Type: application/json" \
  -d '{"start_date": "20240101", "end_date": "20241231", "limit": 100}'

# Match personnel
curl -X POST "http://localhost:8000/matching_yoin" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Python developer needed",
    "anken": "{\"name\":\"Python開発\",\"skill\":\"Python,Django\",\"station\":\"東京\",\"price\":\"50万円\",\"etc\":\"\"}"
  }'
```



以下は、作成したプロジェクトの日本語での解説です。DifyのワークフローをLangChainおよび関連ライブラリで再現した内容について詳しく説明します。

## プロジェクトの概要

このプロジェクトは、Difyで作成されたジョブマッチングワークフローを、LangChainと関連ライブラリを使ってPythonで再現したものです。元のDifyワークフローから「テストフロー」を除いた4つのフローを実装しています。

### 実装されたワークフロー

1. **構造化フロー（要員） - `format_yoin`**
   - Google Apps Script（GAS）から要員のメールデータを取得
   - LangChainのLLMを使って、メール本文から構造化された情報を抽出（氏名、年齢、スキル、最寄駅、勤務形態、単価、備考など）
   - 構造化データをスプレッドシートに書き戻す

2. **構造化フロー（案件） - `format_anken`**
   - 要員の構造化フローと同様に、案件のメールデータを処理
   - 案件名、必須スキル、作業場所、勤務形態、期間、単価、備考などを抽出

3. **RAG登録フロー（要員） - `index_yoin`**
   - 構造化済みの要員データをGASから取得
   - 各要員の情報をRAG（Retrieval-Augmented Generation）用のテキストに整形
   - OpenAIの埋め込み（embedding）を使ってPineconeベクトルデータベースに登録

4. **要員マッチフロー - `matching_yoin`**
   - 案件情報を入力として受け取る
   - Pineconeで類似の要員をベクトル検索
   - LLMを使ってマッチ度を評価し、上位候補と推奨アクションを出力

## プロジェクトの構成

- **`job_matching_flow.py`**: メインスクリプト。すべてのワークフローロジックを実装
- **`.env`**: APIキーなどの環境変数を設定するファイル
- **`README.md`**: 使用方法のドキュメント
- **`requirements.txt`**: 必要なPythonライブラリのリスト

## 主な特徴

- **LangChainの活用**: ChatOpenAIでLLM処理、PineconeVectorStoreでベクトルデータベース操作
- **構造化データ**: Pydanticモデルを使ってデータのバリデーション
- **エラーハンドリング**: 適切な例外処理とログ出力
- **環境変数管理**: python-dotenvを使ってAPIキーを安全に管理

## セットアップ方法

1. **依存関係のインストール**:
   ```bash
   pip install -r requirements.txt
   ```

2. **環境変数の設定**:
   `.env`ファイルに以下のAPIキーを設定してください：
   - `OPENAI_API_KEY`: OpenAIのAPIキー
   - `PINECONE_API_KEY`: PineconeのAPIキー
   - `PINECONE_INDEX_HOST`: PineconeのインデックスホストURL

## 使用方法

ターミナルで以下のコマンドを実行してください：

### 1. 要員データの構造化
```bash
python job_matching_flow.py format_yoin start_date=20240101 end_date=20241231 limit=100
```

### 2. 案件データの構造化
```bash
python job_matching_flow.py format_anken start_date=20240101 end_date=20241231 limit=100
```

### 3. 要員データのRAG登録
```bash
python job_matching_flow.py index_yoin start_date=20240101 end_date=20241231 limit=100
```

### 4. 要員マッチング
```bash
python job_matching_flow.py matching_yoin query="Python開発者募集" anken='{"案件名":"Python開発","必須スキル":"Python,Django","作業場所":"東京","単価":"50万円","備考":""}'
```

## 技術的なポイント

- **LLMプロンプト**: 元のDifyワークフローと同じプロンプトテンプレートを使用
- **ベクトル検索**: Pineconeを使って高速な類似度検索を実現
- **データフロー**: GASとの連携をrequestsライブラリで実装
- **出力形式**: JSON形式で構造化された結果を出力

この実装により、Difyのノードベースのワークフローを、Pythonのスクリプトとしてより柔軟に実行できるようになりました。LangChainの抽象化により、LLMやベクトルデータベースの操作が簡潔に記述されています。

## メモ
### このプロジェクトに関するDifyに対するLangChainの優位性
- データ構造とバリデーション方法が明確、安全
- コードベースなのでチーム開発に向く
- セルフホストすれば制限なし（Difyクラウド版は各種制限がある）
- デバッグ、動作確認、制御がおそらくやりやすい
- AIコーディングとの親和性が高い

### Difyの優位性
- フローが図示されていて明快、説明しやすい（分岐が多いフローで差が出る）
- スタートしやすい、10分でフローが作れる
- チャットボットがすぐ公開できる（フローよりもチャットボット向け？）

## API使用方法

このアプリケーションはFastAPIサーバーとしても実行でき、外部からのアクセスが可能です。

### APIサーバーの起動

```bash
# 開発モード
python main.py

# またはuvicornコマンド
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### APIエンドポイント

- **POST /format_yoin**: 要員データの構造化
- **POST /format_anken**: 案件データの構造化
- **POST /index_yoin**: 要員データをベクトルDBに登録
- **POST /matching_yoin**: 要員と案件のマッチング
- **GET /health**: ヘルスチェック

### APIドキュメント

サーバー起動後、以下のURLでAPIドキュメントを確認できます：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### API呼び出し例

```bash
# 要員データの構造化
curl -X POST "http://localhost:8000/format_yoin" \
  -H "Content-Type: application/json" \
  -d '{"start_date": "20240101", "end_date": "20241231", "limit": 100}'

# 要員マッチング
curl -X POST "http://localhost:8000/matching_yoin" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Python開発者募集",
    "anken": "{\"name\":\"Python開発\",\"skill\":\"Python,Django\",\"station\":\"東京\",\"price\":\"50万円\",\"etc\":\"\"}"
  }'
```

### APIの利点

- **外部連携**: GASや他のシステムから簡単に呼び出し可能
- **スケーラビリティ**: 負荷分散やコンテナ化が容易
- **保守性**: APIドキュメントの自動生成、型チェック
- **拡張性**: ミドルウェア、認証、キャッシュなどの追加が簡単
