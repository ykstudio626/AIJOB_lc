#!/usr/bin/env python3
"""
Google AI Studio（Gemini API）で利用可能なモデル一覧を取得するスクリプト
"""

import os
from dotenv import load_dotenv
import google.generativeai as genai

def main():
    # .envファイルを読み込み
    load_dotenv()
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print('Error: GEMINI_API_KEY not found in .env file')
        print('Please set your Google AI Studio API key in the .env file:')
        print('GEMINI_API_KEY=your_api_key_here')
        return
    
    try:
        # Google Generative AI APIを設定
        genai.configure(api_key=api_key)
        
        print('Google AI Studio で利用可能なモデル:')
        print('=' * 50)
        
        # モデル一覧を取得
        models = genai.list_models()
        
        for model in models:
            if 'generateContent' in model.supported_generation_methods:
                print(f'✓ {model.name}')
                print(f'  Description: {model.description}')
                print(f'  Input token limit: {model.input_token_limit}')
                print(f'  Output token limit: {model.output_token_limit}')
                print('-' * 40)
                
    except Exception as e:
        print(f'Error accessing Google AI Studio API: {e}')
        print('\n一般的なGoogle AI Studioモデル名:')
        print('- models/gemini-pro')
        print('- models/gemini-1.5-pro-latest') 
        print('- models/gemini-1.5-flash-latest')
        print('- models/gemini-1.0-pro')
        print('\nAPI keyが正しく設定されているか確認してください。')

if __name__ == '__main__':
    main()