# FastAPIアプリのエントリーポイント
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn
import json
import asyncio

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
        from job_matching_flow import matching_yoin_flow
        result = matching_yoin_flow(request.anken)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/matching_yoin_stream")
async def api_matching_yoin_stream(request: MatchingRequest):
    """要員マッチングAPI（ストリーミング対応）"""
    async def generate_stream():
        try:
            # 初期化メッセージ
            yield f"data: {json.dumps({'type': 'status', 'message': '検索を開始しています...'}, ensure_ascii=False)}\n\n"
            
            from job_matching_flow import matching_yoin_flow_stream
            
            # ストリーミング処理を実行
            async for chunk in matching_yoin_flow_stream(request.inputs.anken, request.inputs.mode):
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            
            # 完了メッセージ
            yield f"data: {json.dumps({'type': 'complete', 'message': 'マッチング処理が完了しました'}, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            # エラーメッセージ
            error_data = {
                'type': 'error',
                'message': f'エラーが発生しました: {str(e)}'
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*"
        }
    )

@app.post("/matching_yoin_raw_stream")
async def api_matching_yoin_raw_stream(request_data: dict):
    """要員マッチングAPI (Raw JSON対応・ストリーミング)"""
    async def generate_stream():
        try:
            # userInputフィールドから実際のJSONを取得
            if "userInput" in request_data:
                user_input = json.loads(request_data["userInput"])
            else:
                user_input = request_data
            
            # Extract data from nested structure
            if "inputs" in user_input:
                inputs = user_input["inputs"]
                anken = inputs.get("anken", "")
                mode = inputs.get("mode", None)
            else:
                anken = user_input.get("anken", "")
                mode = user_input.get("mode", None)
            
            # 初期化メッセージ
            yield f"data: {json.dumps({'type': 'status', 'message': '検索を開始しています...', 'anken_info': {'案件名': json.loads(anken).get('案件名', '未指定')}, 'mode': mode}, ensure_ascii=False)}\n\n"
            
            from job_matching_flow import matching_yoin_flow_stream
            
            # ストリーミング処理を実行
            async for chunk in matching_yoin_flow_stream(anken, mode):
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            
            # 完了メッセージ
            yield f"data: {json.dumps({'type': 'complete', 'message': 'マッチング処理が完了しました'}, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            error_data = {
                'type': 'error',
                'message': f'エラーが発生しました: {str(e)}'
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*"
        }
    )

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