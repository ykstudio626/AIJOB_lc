# Google AI Studio (Gemini API) セットアップガイド

## 必要なパッケージ

```bash
# Google AI Studio (Gemini API) 用
pip install langchain-google-genai

# AWS Bedrock用 (必要に応じて)
pip install langchain-aws boto3

# その他の既存依存関係
pip install langchain-openai langchain-pinecone
```

## Google AI Studio APIキーの取得

1. [Google AI Studio](https://aistudio.google.com/) にアクセス
2. 「Get API key」をクリック
3. 新しいプロジェクトを作成するか、既存のプロジェクトを選択
4. APIキーを生成
5. `.env`ファイルに設定:

```env
GEMINI_API_KEY=your_actual_api_key_here
LLM_PROVIDER=ai_studio
LLM_MODEL=gemini_flash
```

## 速度とコストの比較

### 推奨設定（速度重視）
```env
LLM_PROVIDER=ai_studio
LLM_MODEL=gemini_flash_8b
GEMINI_API_KEY=your_api_key
```

### 推奨設定（バランス型）
```env
LLM_PROVIDER=ai_studio
LLM_MODEL=gemini_flash
GEMINI_API_KEY=your_api_key
```

### 従来設定（OpenAI）
```env
LLM_PROVIDER=openai
LLM_MODEL=gpt4o_mini
```

## 利用可能なモデル確認

```bash
python llm_config.py
```

## 注意事項

- Google AI StudioはVertex AIよりもセットアップが簡単
- APIキーベースでアクセス可能（GCPプロジェクト設定不要）
- レート制限があるため、本格運用時は制限を確認
- Vertex AIよりもコストが安い場合が多い