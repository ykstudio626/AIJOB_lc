# FastAPIアプリのエントリーポイント
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import Pydantic models
from models import (
    WorkflowParams, 
    MatchingRequest, 
    SuccessResponse, 
    MatchingResponse, 
    HealthResponse
)

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

@app.post("/format_yoin", response_model=SuccessResponse)
async def api_format_yoin(params: WorkflowParams = Body(default=None)):
    """要員データ構造化API"""
    try:
        from job_matching_flow import format_yoin_flow
        if params is None:
            params = WorkflowParams()
        params_dict = params.model_dump()
        format_yoin_flow(params_dict)
        return {"status": "success", "message": "要員データ構造化完了"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/format_anken", response_model=SuccessResponse)
async def api_format_anken(params: WorkflowParams = Body(default=None)):
    """案件データ構造化API"""
    try:
        from job_matching_flow import format_anken_flow
        if params is None:
            params = WorkflowParams()
        params_dict = params.model_dump()
        format_anken_flow(params_dict)
        return {"status": "success", "message": "案件データ構造化完了"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/index_yoin", response_model=SuccessResponse)
async def api_index_yoin(params: WorkflowParams = Body(default=None)):
    """要員データRAG登録API"""
    try:
        from job_matching_flow import index_yoin_flow
        if params is None:
            params = WorkflowParams()
        params_dict = params.model_dump()
        index_yoin_flow(params_dict)
        return {"status": "success", "message": "要員データRAG登録完了"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/matching_yoin", response_model=MatchingResponse)
async def api_matching_yoin(request: MatchingRequest):
    """要員マッチングAPI"""
    try:
        print(f"*******************Received request: {request}")
        print(f"*******************inputs: {request.inputs}")
        print(f"*******************mode: {request.inputs.mode}")
        from job_matching_flow import matching_yoin_flow
        result = matching_yoin_flow(request.inputs.anken, request.inputs.mode)
        return {"status": "success", "result": result}
    except Exception as e:
        print(f"*******************Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/matching_yoin_raw")
async def api_matching_yoin_raw(request_data: dict):
    """要員マッチングAPI (Raw JSON対応)"""
    try:
        print(f"*******************Raw request: {request_data}")
        
        # Extract data from nested structure
        if "inputs" in request_data:
            inputs = request_data["inputs"]
            anken = inputs.get("anken", "")
            mode = inputs.get("mode", None)
        else:
            anken = request_data.get("anken", "")
            mode = request_data.get("mode", None)
        
        print(f"*******************Extracted anken: {anken}")
        print(f"*******************Extracted mode: {mode}")
        
        from job_matching_flow import matching_yoin_flow
        result = matching_yoin_flow(anken, mode)
        return {"status": "success", "result": result}
    except Exception as e:
        print(f"*******************Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {"status": "healthy"}

if __name__ == "__main__":
    # 開発サーバー起動
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )