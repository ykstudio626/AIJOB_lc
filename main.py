# FastAPIアプリのエントリーポイント
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from job_matching_flow import (
    format_yoin_flow,
    format_anken_flow,
    index_yoin_flow,
    matching_yoin_flow
)
import uvicorn

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

if __name__ == "__main__":
    # 開発サーバー起動
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # 開発時のみ
    )