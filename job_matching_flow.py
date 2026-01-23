import os
import json
import requests
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from prompts import MATCHING_PROMPT

# Load environment variables
load_dotenv()

# Constants
GAS_URL = "https://script.google.com/macros/s/AKfycbz2_SYNhkbrBjp1Zv7zB2tQKesGNNtjQGgFBLsl7DmLd3PohCFBG0ZT9ojNReBXa2Zv/exec"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_HOST = os.getenv("PINECONE_INDEX_HOST")

# LLM設定 - 速度改善のためのマルチプロバイダー対応
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # openai, ai_studio, bedrock
LLM_MODEL = os.getenv("LLM_MODEL")  # モデル名（省略時はデフォルト）
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # Google AI Studio Gemini API Key
AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-1")

# 起動時の環境変数デバッグログ
print(f"🔧 [STARTUP] Environment Variables:")
print(f"   LLM_PROVIDER: {LLM_PROVIDER}")
print(f"   LLM_MODEL: {LLM_MODEL}")
print(f"   GEMINI_API_KEY: {'***' + GEMINI_API_KEY[-4:] if GEMINI_API_KEY else 'None'}")
print(f"   OPENAI_API_KEY: {'***' + OPENAI_API_KEY[-4:] if OPENAI_API_KEY else 'None'}")

# Initialize LangChain components (遅延初期化)
llm = None
embeddings = None
vectorstore = None

def get_llm(provider=None):
    """高速化対応のマルチプロバイダーLLM取得関数"""
    global llm
    if llm is None:
        from llm_config import get_model_config
        
        current_provider = provider or LLM_PROVIDER
        model_config = get_model_config(current_provider, LLM_MODEL)
        
        print(f"🚀 [LLM_INIT] Provider: {current_provider}, Model: {model_config['model']}")
        
        if current_provider == "ai_studio":
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                llm = ChatGoogleGenerativeAI(
                    model=model_config["model"],
                    temperature=model_config["temperature"],
                    google_api_key=GEMINI_API_KEY
                )
                print(f"✅ [SUCCESS] Using Google AI Studio {model_config['model']}: {model_config['description']}")
            except ImportError:
                print("❌ [ERROR] langchain-google-genai not installed. Falling back to OpenAI.")
                current_provider = "openai"
                model_config = get_model_config("openai", "gpt4o_mini")
        
        elif current_provider == "bedrock":
            try:
                from langchain_aws import ChatBedrock
                llm = ChatBedrock(
                    model_id=model_config["model_id"],
                    region_name=model_config.get("region_name", AWS_REGION),
                    model_kwargs={"temperature": model_config["temperature"]}
                )
                print(f"✅ [SUCCESS] Using AWS Bedrock {model_config['model_id']}: {model_config['description']}")
            except ImportError:
                print("❌ [ERROR] langchain-aws not installed. Falling back to OpenAI.")
                current_provider = "openai"
                model_config = get_model_config("openai", "gpt4o_mini")
        
        if current_provider == "openai":
            llm = ChatOpenAI(
                model=model_config["model"], 
                temperature=model_config["temperature"], 
                api_key=OPENAI_API_KEY
            )
            print(f"✅ [FALLBACK] Using OpenAI {model_config['model']}: {model_config['description']}")
    
    return llm

def get_embeddings():
    global embeddings
    if embeddings is None:
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small", api_key=OPENAI_API_KEY)
    return embeddings

def get_vectorstore():
    global vectorstore
    if vectorstore is None:
        vectorstore = PineconeVectorStore.from_existing_index(
            index_name="yoin-index",
            embedding=get_embeddings(),
            pinecone_api_key=PINECONE_API_KEY,
            host=PINECONE_INDEX_HOST
        )
    return vectorstore

# Pydantic models for structured output
class YoinStructured(BaseModel):
    id: str = Field(description="ID")
    date: str = Field(description="受信日時")
    name: str = Field(description="氏名")
    age: str = Field(description="年齢")
    skill: str = Field(description="スキル")
    station: str = Field(description="最寄駅")
    work_style: str = Field(description="勤務形態")
    price: str = Field(description="単価")
    etc: str = Field(description="備考")
    subject: str = Field(description="件名")

class AnkenStructured(BaseModel):
    id: str = Field(description="ID")
    date: str = Field(description="受信日時")
    name: str = Field(description="案件名")
    skill: str = Field(description="必須スキル")
    station: str = Field(description="作業場所")
    work_style: str = Field(description="勤務形態")
    schedule: str = Field(description="期間")
    price: str = Field(description="単価")
    etc: str = Field(description="備考")
    subject: str = Field(description="件名")

class MatchCandidate(BaseModel):
    yoin_id: str
    date: str
    yoin_info: Dict[str, Any]
    match_score: int
    comment: str

class MatchingResult(BaseModel):
    candidates: List[MatchCandidate]
    comparision: List[Dict[str, Any]]
    actions: List[str]

def get_data_from_gas(type_: str, params: Dict[str, Any] = None) -> Dict:
    """GASからデータを取得"""
    url = f"{GAS_URL}?type={type_}"
    if params:
        param_str = "&".join([f"{k}={v}" for k, v in params.items() if v])
        url += f"&{param_str}"
    
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def post_data_to_gas(type_: str, data: Dict) -> Dict:
    """GASにデータをPOST"""
    print("data", data)
    url = f"{GAS_URL}?type={type_}"
    response = requests.post(url, json=data)
    response.raise_for_status()
    return response.json()

def format_yoin_item(item: Dict) -> str:
    """要員アイテムをプロンプト用テキストに整形"""
    return f"""
以下は要員情報メールです。
ID: {item.get('ID', '')}
受信日時: {item.get('受信日時', '')}
件名: {item.get('件名', '')}
本文:
{item.get('本文', '')}
"""

def format_anken_item(item: Dict) -> str:
    """案件アイテムをプロンプト用テキストに整形"""
    return f"""
以下は案件情報メールです。
ID: {item.get('ID', '')}
受信日時: {item.get('受信日時', '')}
件名: {item.get('件名', '')}
本文:
{item.get('本文', '')}
"""

def structure_yoin_data(raw_text: str, item: Dict) -> Dict:
    """要員データを構造化"""
    prompt_text = f"""
あなたはITエンジニア派遣の「要員情報」を整理するアシスタントです。

以下に入力として「メール本文」「メールID」「受信日時」「件名」「本文」が与えられます。
これらの情報をもとに、要員情報を正確に抽出してください。

入力情報:
{raw_text}

必ず次のJSON形式で出力してください：

{{
  "id": "（ここに上記のidをそのまま記入）",
  "date": "（ここに上記の受信日時をそのまま記入）",
  "name": "（ここに要員のイニシャルを記入）",
  "age":"（ここに要員の年齢を記入）",
  "skill": "（ここに要員のスキルを記入）",
  "station": "（ここに要員の最寄駅）",
  "work_style": "（ここに要員の希望勤務形態を記入）",
  "price": "（ここに要員の希望単価を記入）",
  "etc": "（ここにその他備考を記入）",
  "subject": ""
}}

- 出力は必ず上記のJSONのみで返してください。
- "skill"は箇条書きに変換し、各行の頭に"- "を付加してください
- "name"は「A.B」の形式で、イニシャル以外のテキストは含めないでください。
- コードブロックや説明文は不要です。
- "age"は「歳」「才」などは含めないでください。
- idとdateは絶対に入力値と一致させてください。
"""
    
    # LLMを直接呼び出し
    response = get_llm().invoke(prompt_text)
    
    # JSONパースとPydanticバリデーション
    try:
        # JSON文字列をパース
        json_data = json.loads(response.content)
        # Pydanticモデルを作成
        result = YoinStructured(**json_data)
        return result.model_dump()
    except Exception as e:
        return {"error": f"Parse failed: {e}", "raw_response": response.content}

def structure_anken_data(raw_text: str, item: Dict) -> Dict:
    """案件データを構造化"""
    prompt_text = f"""
あなたはITエンジニア派遣の「案件情報」を整理するアシスタントです。

以下に入力として「メール本文」「メールID」「受信日時」「件名」「本文」が与えられます。
これらの情報をもとに、案件情報を正確に抽出してください。

入力情報:
{raw_text}

必ず次のJSON形式で出力してください：

{{
  "id": "（ここに上記のidをそのまま記入）",
  "date": "（ここに上記の受信日時をそのまま記入）",
  "name": "（ここに案件名を記入）",
  "skill": "",
  "station": "（ここに勤務地の最寄駅を記入）",
  "work_style": "（ここに勤務形態を記入）",
  "schedule": "",
  "price": "（ここに単価、単金を記入）",
  "etc": "（ここにその他備考を記入）",
  "subject": "（ここに件名を記入）"
}}

注意:
- "skill"は要員のスキルを箇条書きに変換し、各行の頭に"- "を付加してください
- "schedule"は「期間」「時期」「開始」「作業開始時期」「作業期間」「スケジュール」などで示されている
- 出力は必ず上記のJSONのみで返してください。
- コードブロックや説明文は不要です。
- idとdateは絶対に入力値と一致させてください。
"""
    
    # LLMを直接呼び出し
    response = get_llm().invoke(prompt_text)
    
    # JSONパースとPydanticバリデーション
    try:
        # JSON文字列をパース
        json_data = json.loads(response.content)
        # Pydanticモデルを作成
        result = AnkenStructured(**json_data)
        return result.model_dump()
    except Exception as e:
        return {"error": f"Parse failed: {e}", "raw_response": response.content}

# 構造化フロー（要員）
def format_yoin_flow(params: Dict[str, Any]):
    """構造化フロー（要員）"""
    print("Starting format_yoin flow...")
    
    # with_indexパラメータをチェック
    with_index = params.get("with_index", False)
    if isinstance(with_index, str):
        with_index = with_index.lower() == "true"
    
    # Get data from GAS
    data = get_data_from_gas("yoin", params)
    records = data.get("records", [])
    
    for record in records:
        # Format item
        formatted_text = format_yoin_item(record)
        
        # Structure with LLM
        structured = structure_yoin_data(formatted_text, record)
        
        # エラーチェック
        if "error" in structured:
            print(f"Error processing record {record.get('ID', 'unknown')}: {structured['error']}")
            print(f"Raw response: {structured.get('raw_response', '')}")
            continue
        
        # Post back to GAS
        # raw_inputフィールドを追加してメール本文をK列に保存
        structured["raw_input"] = record.get('本文', '')
        post_data = {
            "type": "yoin",
            "record": structured
        }
        post_data_to_gas("yoin", post_data)
        print(f"Processed yoin ID: {structured.get('id', 'unknown')}")
    
    print("format_yoin flow completed.")
    
    # with_index=Trueの場合、続けてRAG登録を実行
    if with_index:
        print("\n--- Starting automatic index_yoin flow ---")
        # paramsからwith_indexを除外してindex_yoin_flowに渡す
        index_params = {k: v for k, v in params.items() if k != "with_index"}
        index_yoin_flow(index_params)
        
# 構造化フロー（案件）
def format_anken_flow(params: Dict[str, Any]):
    """構造化フロー（案件）"""
    print("Starting format_anken flow...")
    
    # Get data from GAS
    data = get_data_from_gas("anken", params)

    records = data.get("records", [])
    
    for record in records:
        raw_text = record["本文"]
        # Format item
        formatted_text = format_anken_item(record)

        # print(formatted_text)
        
        # Structure with LLM
        structured = structure_anken_data(formatted_text, record)
        
        # エラーチェック
        if "error" in structured:
            print(f"Error processing record {record.get('ID', 'unknown')}: {structured['error']}")
            print(f"Raw response: {structured.get('raw_response', '')}")
            continue
        
        # raw_inputフィールドを追加してメール本文をK列に保存
        structured["raw_input"] = record.get('本文', '')

        print(structured)
        
        # Post back to GAS
        post_data = {
            "type": "anken",
            "record": structured
        }
        post_data_to_gas("anken", post_data)
        print(f"Processed anken ID: {structured.get('id', 'unknown')}")
    
    print("format_anken flow completed.")

# RAG登録フロー（要員）
def index_yoin_flow(params: Dict[str, Any]):
    """RAG登録フロー（要員）"""
    print("Starting index_yoin flow...")
    
    # Get formatted data from GAS
    data = get_data_from_gas("yoin_format", params)
    records = data.get("records", [])
    
    # Initialize Pinecone vector store
    vectorstore = PineconeVectorStore(
        index_name="yoin2",  # Assuming index name from host
        embedding=get_embeddings(),
        pinecone_api_key=PINECONE_API_KEY
    )
    
    for record in records:
        # Create RAG text
        rag_text = f"""
        【要員ID】 {record.get('ID', '')}
        【受信日時】 {record.get('受信日時', '')}
        【氏名】 {record.get('氏名', '')}
        【年齢】 {record.get('年齢', '')}
        【スキル】 {record.get('スキル', '')}
        【最寄駅】 {record.get('最寄駅', '')}
        【勤務形態（希望）】 {record.get('勤務形態（希望）', '')}
        【単価（希望）】 {record.get('単価（希望）', '')}
        【備考】 {record.get('備考', '')}
        【メールタイトル】 {record.get('メールタイトル', '')}
        """
        
        # Add to vector store
        vectorstore.add_texts(
            texts=[rag_text.strip()],
            ids=[record.get('ID', '')],
            metadatas=[{
                "recieved_at": int(record.get('受信日時', '').replace('-', '')[:8]),
                "text": rag_text.strip()
            }]
        )
        print(f"Indexed yoin ID: {record.get('ID', '')}")
    
    print("index_yoin flow completed.")

# 要員マッチフロー
def matching_yoin_flow(anken: str):
    """要員マッチフロー"""
    print("Starting matching_yoin flow...")
    
    # Parse anken data
    anken_data = json.loads(anken)
    
    # Create search text with weighted keywords (improved approach)
    重点キーワード = anken_data.get('重点キーワード', '')
    
    # より自然な形で重要度を高める
    search_text = f"""
【最重要スキル】: {重点キーワード}
案件名: {anken_data.get('案件名', '')}
求めるスキル: {重点キーワード}
必須スキル: {anken_data.get('必須スキル', '')}
作業場所: {anken_data.get('作業場所', '')}
単価: {anken_data.get('単価', '')}
備考: {anken_data.get('備考', '')}
優先技術: {重点キーワード}
""".strip()
    
    # Initialize Pinecone vector store
    vectorstore = PineconeVectorStore(
        index_name="yoin2",
        embedding=get_embeddings(),
        pinecone_api_key=PINECONE_API_KEY
    )
    
    # Search similar vectors
    docs = vectorstore.similarity_search_with_score(search_text, k=20)
    
    # Format results for LLM
    matches_text = ""
    if docs:
        for doc, score in docs:
            print("debug")
            print(doc.page_content)
            matches_text += f"""
■ 要員ID: {doc.id}
スコア: {score}
{doc.page_content}
-------------------------
""".strip() + "\n"
    else:
        matches_text = "検索結果がありませんでした。"
    
    # LLM matching - マルチプロバイダー対応
    prompt = PromptTemplate.from_template(MATCHING_PROMPT)

    print(f"debug - Using LLM Provider: {LLM_PROVIDER}, Model: {LLM_MODEL or 'default'}")
    print("debug" + MATCHING_PROMPT)
    
    chain = prompt | get_llm() | JsonOutputParser(pydantic_object=MatchingResult)
    result = chain.invoke({
        "anken_formatted": json.dumps(anken_data, ensure_ascii=False),
        "matches_text": matches_text
    })
    
    print("Matching result:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("matching_yoin flow completed.")
    return result

# 要員マッチフロー（ストリーミング対応・高速化版）
async def matching_yoin_flow_stream(anken: str, mode: str = None):
    """要員マッチフロー（ストリーミング対応・マルチプロバイダー対応）"""
    import asyncio
    
    yield {"type": "status", "message": f"案件データを解析中... (Provider: {LLM_PROVIDER}, Model: {LLM_MODEL or 'default'})"}
    await asyncio.sleep(0.1)
    
    # Parse anken data
    anken_data = json.loads(anken)
    
    yield {"type": "status", "message": "検索クエリを作成中..."}
    await asyncio.sleep(0.1)
    
    # Create search text with weighted keywords
    重点キーワード = anken_data.get('重点キーワード', '')
    
    search_text = f"""
【最重要スキル】: {重点キーワード}
案件名: {anken_data.get('案件名', '')}
求めるスキル: {重点キーワード}
必須スキル: {anken_data.get('必須スキル', '')}
作業場所: {anken_data.get('作業場所', '')}
単価: {anken_data.get('単価', '')}
備考: {anken_data.get('備考', '')}
優先技術: {重点キーワード}
""".strip()
    
    yield {"type": "status", "message": "データベースから要員を検索中..."}
    await asyncio.sleep(0.1)
    
    # Initialize Pinecone vector store
    vectorstore = PineconeVectorStore(
        index_name="yoin2",
        embedding=get_embeddings(),
        pinecone_api_key=PINECONE_API_KEY
    )
    
    # Search similar vectors
    docs = vectorstore.similarity_search_with_score(search_text, k=20)
    
    # 見つかった要員のIDリストを作成
    found_yoin_ids = [doc.id for doc, score in docs]
    
    yield {
        "type": "search_complete", 
        "message": f"{len(docs)}件の候補を発見", 
        "count": len(docs),
        "yoin_ids": found_yoin_ids
    }
    await asyncio.sleep(0.1)
    
    # quickモードの場合は検索結果のみ返す
    if mode == "quick":
        formatted_results = []
        for i, (doc, score) in enumerate(docs):
            formatted_results.append({
                "id": doc.id,
                "content": doc.page_content,
                "score": float(score),
                "metadata": doc.metadata
            })
            yield {
                "type": "quick_result",
                "index": i + 1,
                "total": len(docs),
                "result": formatted_results[-1]
            }
            await asyncio.sleep(0.05)
        
        yield {
            "type": "final_result",
            "message": "検索完了",
            "results": {"quick_results": formatted_results}
        }
        return
    
    # 通常モード: LLMでのマッチング分析（高速化対応）
    yield {"type": "status", "message": f"AI分析を開始中... (Using {LLM_PROVIDER}:{LLM_MODEL or 'default'})"}
    await asyncio.sleep(0.1)
    
    # Format results for LLM
    matches_text = ""
    if docs:
        for doc, score in docs:
            matches_text += f"""
■ 要員ID: {doc.id}
スコア: {score}
{doc.page_content}
-------------------------
""".strip() + "\n"
    else:
        matches_text = "検索結果がありませんでした。"
    
    yield {"type": "status", "message": "マッチング分析中..."}
    await asyncio.sleep(0.1)
    
    # LLM matching with streaming - マルチプロバイダー対応
    prompt = PromptTemplate.from_template(MATCHING_PROMPT)
    
    # ストリーミング対応のLLM作成（設定ファイルベース）
    from llm_config import get_model_config
    model_config = get_model_config(LLM_PROVIDER, LLM_MODEL)
    
    if LLM_PROVIDER == "ai_studio":
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm_stream = ChatGoogleGenerativeAI(
                model=model_config["model"],
                temperature=model_config["temperature"],
                google_api_key=GEMINI_API_KEY,
                streaming=True
            )
        except ImportError:
            from langchain_openai import ChatOpenAI
            fallback_config = get_model_config("openai", "gpt4o_mini")
            llm_stream = ChatOpenAI(
                model=fallback_config["model"], 
                temperature=fallback_config["temperature"], 
                api_key=OPENAI_API_KEY,
                streaming=True
            )
    elif LLM_PROVIDER == "bedrock":
        try:
            from langchain_aws import ChatBedrock
            llm_stream = ChatBedrock(
                model_id=model_config["model_id"],
                region_name=model_config.get("region_name", AWS_REGION),
                model_kwargs={"temperature": model_config["temperature"]},
                streaming=True
            )
        except ImportError:
            from langchain_openai import ChatOpenAI
            fallback_config = get_model_config("openai", "gpt4o_mini")
            llm_stream = ChatOpenAI(
                model=fallback_config["model"], 
                temperature=fallback_config["temperature"], 
                api_key=OPENAI_API_KEY,
                streaming=True
            )
    else:  # OpenAI
        from langchain_openai import ChatOpenAI
        llm_stream = ChatOpenAI(
            model=model_config["model"], 
            temperature=model_config["temperature"], 
            api_key=OPENAI_API_KEY,
            streaming=True
        )
    
    chain = prompt | llm_stream
    
    # ストリーミングでLLMレスポンスを処理
    accumulated_response = ""
    async for chunk in chain.astream({
        "anken_formatted": json.dumps(anken_data, ensure_ascii=False),
        "matches_text": matches_text
    }):
        if chunk.content:
            accumulated_response += chunk.content
            yield {
                "type": "llm_chunk",
                "content": chunk.content,
                "accumulated": accumulated_response
            }
    
    yield {"type": "status", "message": "分析結果を整理中..."}
    await asyncio.sleep(0.1)
    
    # Parse final JSON result
    try:
        # JSONパーサーで最終結果を解析
        from langchain_core.output_parsers import JsonOutputParser
        parser = JsonOutputParser(pydantic_object=MatchingResult)
        result = parser.parse(accumulated_response)
        
        yield {
            "type": "final_result",
            "message": "マッチング分析完了",
            "result": result
        }
    except Exception as e:
        yield {
            "type": "error",
            "message": f"結果の解析に失敗しました: {str(e)}",
            "raw_response": accumulated_response
        }

def main(action: str, **kwargs):
    """メイン関数"""
    params = {
        "start_date": kwargs.get("start_date"),
        "end_date": kwargs.get("end_date"),
        "limit": kwargs.get("limit"),
        "offset": kwargs.get("offset"),
        "with_index": kwargs.get("with_index")
    }
    
    if action == "format_yoin":
        format_yoin_flow(params)
    elif action == "format_anken":
        format_anken_flow(params)
    elif action == "index_yoin":
        index_yoin_flow(params)
    elif action == "matching_yoin":
        matching_yoin_flow(kwargs.get("anken", ""))
    elif action == "matching_yoin_stream":
        # ストリーミング版の実行（asyncio対応）
        import asyncio
        async def run_stream():
            async for chunk in matching_yoin_flow_stream(
                kwargs.get("anken", ""), 
                kwargs.get("mode", None)
            ):
                print(f"Stream chunk: {chunk}")
        
        asyncio.run(run_stream())
    else:
        print(f"Unknown action: {action}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python job_matching_flow.py <action> [kwargs...]")
        print("Actions: format_yoin, format_anken, index_yoin, matching_yoin, matching_yoin_stream")
        sys.exit(1)
    
    action = sys.argv[1]
    kwargs = {}
    for arg in sys.argv[2:]:
        if "=" in arg:
            key, value = arg.split("=", 1)
            kwargs[key] = value
    
    main(action, **kwargs)