# FastAPI導入ガイド

このガイドでは、既存のジョブマッチングワークフロー（`job_matching_flow.py`）にFastAPIを導入し、外部からHTTPリクエストで起動できるAPIに変換する手順を説明します。

## 概要

現在のスクリプトはコマンドラインから実行する形式ですが、FastAPIを導入することで：
- HTTP APIとして各ワークフローを呼び出せるようになります
- 外部システム（GAS、Webアプリなど）からの統合が容易になります
- 非同期処理やミドルウェアの導入が可能になります

## 手順

### 1. 依存関係の更新

`requirements.txt`にFastAPIとUvicornを追加します：

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
```

### 2. コードの構造変更

`job_matching_flow.py`を以下のように変更します：

#### 2.1 インポート追加
```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
```

#### 2.2 FastAPIアプリの初期化
```python
app = FastAPI(
    title="Job Matching API",
    description="ジョブマッチングワークフローのAPI",
    version="1.0.0"
)

# CORS設定（必要に応じて）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切なオリジンを指定
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 2.3 既存のメイン関数をAPIエンドポイントに変換

各ワークフローを個別のエンドポイントとして定義：

```python
@app.post("/format_yoin")
async def api_format_yoin(params: dict = None):
    """要員データ構造化API"""
    try:
        if params is None:
            params = {}
        format_yoin_flow(params)
        return {"status": "success", "message": "要員データ構造化完了"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/format_anken")
async def api_format_anken(params: dict = None):
    """案件データ構造化API"""
    try:
        if params is None:
            params = {}
        format_anken_flow(params)
        return {"status": "success", "message": "案件データ構造化完了"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/index_yoin")
async def api_index_yoin(params: dict = None):
    """要員データRAG登録API"""
    try:
        if params is None:
            params = {}
        index_yoin_flow(params)
        return {"status": "success", "message": "要員データRAG登録完了"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/matching_yoin")
async def api_matching_yoin(request: dict):
    """要員マッチングAPI"""
    try:
        query = request.get("query", "")
        anken = request.get("anken", "{}")
        result = matching_yoin_flow(query, anken)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {"status": "healthy"}
```

#### 2.4 メイン実行部分の変更

```python
if __name__ == "__main__":
    # 開発サーバー起動
    uvicorn.run(
        "job_matching_flow:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # 開発時のみ
    )
```

### 3. 起動方法

#### 開発環境
```bash
# 直接実行
python job_matching_flow.py

# またはuvicornコマンド
uvicorn job_matching_flow:app --reload --host 0.0.0.0 --port 8000
```

#### 本番環境
```bash
# バックグラウンド実行
uvicorn job_matching_flow:app --host 0.0.0.0 --port 8000

# またはsystemdなどで管理
```

### 4. APIドキュメント

FastAPIは自動的にAPIドキュメントを生成します：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 5. 使用例

#### 要員データ構造化
```bash
curl -X POST "http://localhost:8000/format_yoin" \
  -H "Content-Type: application/json" \
  -d '{"start_date": "20240101", "end_date": "20241231", "limit": 100}'
```

#### 要員マッチング
```bash
curl -X POST "http://localhost:8000/matching_yoin" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Python開発者募集",
    "anken": "{\"name\":\"Python開発\",\"skill\":\"Python,Django\",\"station\":\"東京\",\"price\":\"50万円\",\"etc\":\"\"}"
  }'
```

### 6. テスト

#### ユニットテスト
```python
# test_api.py
from fastapi.testclient import TestClient
from job_matching_flow import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
```

#### 実行
```bash
pytest test_api.py
```

### 7. デプロイメント

#### Docker
```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "job_matching_flow:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### AWS EC2デプロイ
```bash
# EC2上で
sudo apt update
sudo apt install python3.12 python3.12-venv nginx

# 仮想環境作成
python3.12 -m venv venv
source venv/bin/activate

# 依存関係インストール
pip install -r requirements.txt

# systemdサービス作成
sudo nano /etc/systemd/system/job-matching.service
```

systemdサービスファイル内容：
```ini
[Unit]
Description=Job Matching API
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/AIJOB_lc
ExecStart=/home/ubuntu/AIJOB_lc/venv/bin/uvicorn job_matching_flow:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# サービス有効化・起動
sudo systemctl enable job-matching
sudo systemctl start job-matching
sudo systemctl status job-matching
```

### 8. セキュリティ考慮事項

- APIキーの適切な管理
- HTTPSの導入（Let's Encryptなど）
- レート制限の実装
- 認証・認可の追加（必要に応じて）
- CORS設定の見直し

### 9. 監視・ログ

- ログの適切な設定
- ヘルスチェックエンドポイントの活用
- エラーハンドリングの強化
- パフォーマンス監視

## 注意点

- 各ワークフローの実行時間が長い場合、非同期処理（`async def`）を検討
- 大量データの処理時は、バックグラウンドタスク（BackgroundTasks）を活用
- 本番環境では`reload=True`を削除
- 環境変数での設定管理を強化

## 移行後の利点

1. **外部連携**: GASや他のシステムから簡単に呼び出し可能
2. **スケーラビリティ**: 負荷分散やコンテナ化が容易
3. **保守性**: APIドキュメントの自動生成、型チェック
4. **拡張性**: ミドルウェア、認証、キャッシュなどの追加が簡単</content>
<parameter name="filePath">/Users/yusukekohno/Documents/AIJOB_lc/fastapi_integration_guide.md