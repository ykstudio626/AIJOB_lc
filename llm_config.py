"""
LLMプロバイダーとモデルの設定マッピング
高速化対応のための各種クラウドサービス・モデル対応表
"""

# 各プロバイダーでサポートされるモデル設定
LLM_MODELS = {
    "openai": {
        "gpt4o_mini": {
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "description": "OpenAI GPT-4o mini（従来モデル）"
        },
        "gpt4o": {
            "model": "gpt-4o",
            "temperature": 0.7,
            "description": "OpenAI GPT-4o（高性能モデル）"
        },
        "gpt35_turbo": {
            "model": "gpt-3.5-turbo",
            "temperature": 0.7,
            "description": "OpenAI GPT-3.5 Turbo（高速モデル）"
        }
    },
    
    "ai_studio": {
        "gemini_flash": {
            "model": "gemini-flash-latest",
            "temperature": 0.7,
            "description": "Google AI Studio Gemini Flash Latest（最高速）"
        },
        "gemini_pro": {
            "model": "gemini-pro-latest",
            "temperature": 0.7,
            "description": "Google AI Studio Gemini Pro Latest（高性能）"
        },
        "gemini_20_flash": {
            "model": "gemini-2.0-flash",
            "temperature": 0.7,
            "description": "Google AI Studio Gemini 2.0 Flash（安定版）"
        },
        "gemini_25_flash": {
            "model": "gemini-2.5-flash",
            "temperature": 0.7,
            "description": "Google AI Studio Gemini 2.5 Flash（最新版）"
        }
    },
    
    "bedrock": {
        "claude_haiku": {
            "model_id": "anthropic.claude-3-haiku-20240307-v1:0",
            "temperature": 0.7,
            "region_name": "ap-northeast-1",
            "description": "AWS Bedrock Claude 3 Haiku（最高速）"
        },
        "claude_sonnet": {
            "model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
            "temperature": 0.7,
            "region_name": "ap-northeast-1",
            "description": "AWS Bedrock Claude 3 Sonnet（バランス型）"
        },
        "titan_text": {
            "model_id": "amazon.titan-text-express-v1",
            "temperature": 0.7,
            "region_name": "ap-northeast-1",
            "description": "AWS Bedrock Titan Text Express（高速）"
        },
        "titan_text_lite": {
            "model_id": "amazon.titan-text-lite-v1",
            "temperature": 0.7,
            "region_name": "ap-northeast-1", 
            "description": "AWS Bedrock Titan Text Lite（軽量高速）"
        }
    }
}

# デフォルト設定
DEFAULT_MODELS = {
    "openai": "gpt4o_mini",
    "ai_studio": "gemini_pro", 
    "bedrock": "claude_haiku"
}

# 速度順ランキング（推定）
SPEED_RANKING = [
    ("ai_studio", "gemini_flash"),
    ("bedrock", "claude_haiku"),
    ("ai_studio", "gemini_pro"),
    ("bedrock", "titan_text_lite"),
    ("bedrock", "titan_text"),
    ("openai", "gpt35_turbo"),
    ("ai_studio", "gemini_15_pro"),
    ("bedrock", "claude_sonnet"),
    ("openai", "gpt4o_mini"),
    ("openai", "gpt4o")
]

def get_model_config(provider: str, model_name: str = None):
    """
    指定されたプロバイダーとモデル名の設定を取得
    
    Args:
        provider: LLMプロバイダー (openai, ai_studio, bedrock)
        model_name: モデル名 (省略時はデフォルトを使用)
    
    Returns:
        dict: モデル設定辞書
    """
    if provider not in LLM_MODELS:
        raise ValueError(f"Unsupported provider: {provider}")
    
    if model_name is None:
        model_name = DEFAULT_MODELS.get(provider)
    
    if model_name not in LLM_MODELS[provider]:
        available_models = list(LLM_MODELS[provider].keys())
        raise ValueError(f"Unsupported model '{model_name}' for provider '{provider}'. Available models: {available_models}")
    
    return LLM_MODELS[provider][model_name]

def list_available_models():
    """利用可能な全モデルのリストを表示"""
    print("=== Available LLM Models ===")
    for provider, models in LLM_MODELS.items():
        print(f"\n{provider.upper()}:")
        for model_name, config in models.items():
            print(f"  - {model_name}: {config['description']}")
    
    print(f"\n=== Speed Ranking (Fastest to Slowest) ===")
    for i, (provider, model) in enumerate(SPEED_RANKING, 1):
        config = LLM_MODELS[provider][model]
        print(f"{i:2d}. {provider}:{model} - {config['description']}")

if __name__ == "__main__":
    list_available_models()