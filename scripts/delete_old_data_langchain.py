#!/usr/bin/env python3
"""
LangChain経由でPineconeの古いデータを削除
2026/1/9以前の要員データを削除します
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore

# 環境変数読み込み
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "yoin2"

def delete_old_data_langchain():
    """LangChain経由で古いデータを削除"""
    
    try:
        # Embeddings初期化
        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=OPENAI_API_KEY
        )
        
        # PineconeVectorStore初期化
        vectorstore = PineconeVectorStore(
            index_name=INDEX_NAME,
            embedding=embeddings,
            pinecone_api_key=PINECONE_API_KEY
        )
        
        print(f"📊 Pineconeインデックス '{INDEX_NAME}' に接続完了")
        
        # 削除対象日付
        cutoff_date = datetime(2026, 1, 9)
        cutoff_str = cutoff_date.strftime('%Y/%m/%d')
        
        print(f"🗓️  削除対象: recieved_at < 20260109 のデータ")
        
        # 確認
        confirm = input(f"\n⚠️  recieved_at < 20260109 のデータを削除しますか？ (yes/no): ")
        if confirm.lower() not in ['yes', 'y']:
            print("🚫 削除をキャンセルしました")
            return False
        
        # メタデータフィルターで削除
        # recieved_atフィールドでフィルタリング（数値型）
        filter_conditions = [
            {"recieved_at": {"$lt": 20260109}},
            {"recieved_at": {"$lte": 20260108}},
        ]
        
        deleted_total = 0
        
        for i, filter_condition in enumerate(filter_conditions):
            try:
                print(f"🔄 フィルター {i+1}/3 で削除中...")
                
                # PineconeVectorStoreのdelete()メソッド使用
                # 注意: バージョンによって使用可能なメソッドが異なります
                delete_response = vectorstore.delete(filter=filter_condition)
                
                if delete_response:
                    print(f"✅ フィルター {i+1} 削除完了")
                    deleted_total += 1
                else:
                    print(f"ℹ️  フィルター {i+1} 削除対象なし")
                    
            except Exception as e:
                print(f"⚠️  フィルター {i+1} 削除失敗: {e}")
        
        print(f"\n📊 削除処理完了")
        print(f"   適用フィルター数: {deleted_total}/{len(filter_conditions)}")
        
        return True
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return False

def main():
    """メイン処理"""
    print("🗑️  Pinecone 古いデータ削除ツール (LangChain版)")
    print("=" * 50)
    
    if not OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY が設定されていません")
        return
    
    if not PINECONE_API_KEY:
        print("❌ PINECONE_API_KEY が設定されていません")
        return
    
    if delete_old_data_langchain():
        print("\n✅ 削除処理完了")
    else:
        print("\n❌ 削除処理失敗")

if __name__ == "__main__":
    main()