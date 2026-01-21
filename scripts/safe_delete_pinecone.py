#!/usr/bin/env python3
"""
安全なPineconeデータ削除スクリプト
まずデータを確認してから削除を実行
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore

load_dotenv()

# 削除対象日付の設定
DELETE_BEFORE_DATE = 20260115  # この日付より前のデータを削除

def safe_delete_old_data():
    """安全にデータを確認・削除"""
    
    # 環境変数チェック
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    
    if not OPENAI_API_KEY or not PINECONE_API_KEY:
        print("❌ API キーが設定されていません")
        return False
    
    try:
        # 初期化
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small", api_key=OPENAI_API_KEY)
        vectorstore = PineconeVectorStore(
            index_name="yoin2",
            embedding=embeddings,
            pinecone_api_key=PINECONE_API_KEY
        )
        
        print("📊 Pinecone接続完了")
        
        # 削除対象日時
        cutoff_date = datetime(2026, 1, 9)
        
        print(f"🗓️  削除対象: recieved_at < {DELETE_BEFORE_DATE} のデータ")
        
        # Step 1: 削除件数を事前確認
        print("\n🔍 削除対象件数を確認中...")
        
        # 削除対象をカウント（実際の削除は行わない）
        delete_filters = [
            {"recieved_at": {"$lt": DELETE_BEFORE_DATE}},    # 数値型での比較
            {"recieved_at": {"$lte": DELETE_BEFORE_DATE - 1}},   # DELETE_BEFORE_DATE-1以下
        ]
        
        # 削除対象のデータを検索して件数を確認
        try:
            # 削除対象データを検索（多めに取得して件数確認）
            old_docs = vectorstore.similarity_search_with_score("", k=1000)
            delete_count = 0
            total_count = len(old_docs)
            
            for doc, score in old_docs:
                recieved_at = doc.metadata.get('recieved_at')
                if recieved_at and isinstance(recieved_at, (int, float)) and int(recieved_at) < DELETE_BEFORE_DATE:
                    delete_count += 1
            
            print(f"📊 データ件数確認結果:")
            print(f"  総データ数: {total_count}件")
            print(f"  削除対象: {delete_count}件")
            print(f"  保持対象: {total_count - delete_count}件")
            
            if delete_count == 0:
                print("\n✅ 削除対象のデータがありません")
                return True
                
        except Exception as e:
            print(f"⚠️ 件数確認でエラーが発生しました: {e}")
            print("削除処理を続行しますか？")
        
        # Step 2: 削除確認
        print(f"\n⚠️ {delete_count}件のデータを削除しますか？")
        print("   この操作は元に戻せません。")
        confirm = input("   削除実行しますか？ (y/N): ")
        
        if confirm.lower() not in ['y', 'yes']:
            print("🚫 削除をキャンセルしました")
            return False
        
        # Step 3: 削除実行
        print("🗑️  削除を実行中...")
        
        success_count = 0
        for i, delete_filter in enumerate(delete_filters):
            try:
                print(f"  フィルター {i+1}: {delete_filter}")
                # 実際の削除を実行
                result = vectorstore.delete(filter=delete_filter)
                print(f"  → 削除完了: {result}")
                success_count += 1
            except Exception as e:
                print(f"  → エラー: {e}")
        
        print(f"\n✅ 削除処理完了 ({success_count}/{len(delete_filters)} フィルター成功)")
        
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

if __name__ == "__main__":
    print("🛡️  安全なPineconeデータ削除ツール")
    print("=" * 40)
    safe_delete_old_data()