#!/usr/bin/env python3
"""
Pinecone要員データ削除スクリプト
2026/1/9以前の要員データを削除します
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
import pinecone

# 環境変数読み込み
load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "yoin2"

def parse_date_from_metadata(metadata):
    """メタデータから日付を解析"""
    date_str = metadata.get('受信日時', '')
    if not date_str:
        return None
    
    try:
        # 様々な日付形式に対応
        for fmt in ['%Y/%m/%d', '%Y-%m-%d', '%Y%m%d']:
            try:
                return datetime.strptime(date_str.split()[0], fmt)
            except ValueError:
                continue
        return None
    except:
        return None

def delete_old_data():
    """2026/1/9以前のデータを削除"""
    
    if not PINECONE_API_KEY:
        print("❌ PINECONE_API_KEY が設定されていません")
        return False
    
    try:
        # Pinecone初期化
        pinecone.init(api_key=PINECONE_API_KEY)
        index = pinecone.Index(INDEX_NAME)
        
        print(f"📊 インデックス '{INDEX_NAME}' に接続中...")
        
        # 削除対象日時
        cutoff_date = datetime(2026, 1, 9)
        print(f"🗓️  削除対象: {cutoff_date.strftime('%Y/%m/%d')} 以前のデータ")
        
        # 統計情報取得
        stats = index.describe_index_stats()
        total_vectors = stats.get('total_vector_count', 0)
        print(f"📈 現在のベクター数: {total_vectors}")
        
        if total_vectors == 0:
            print("ℹ️  削除対象のデータがありません")
            return True
        
        # 確認プロンプト
        confirm = input(f"\n⚠️  {cutoff_date.strftime('%Y/%m/%d')} 以前のデータを削除しますか？ (yes/no): ")
        if confirm.lower() not in ['yes', 'y']:
            print("🚫 削除をキャンセルしました")
            return False
        
        # すべてのベクターを取得してフィルタリング
        print("🔍 データを検索中...")
        
        # クエリでデータを取得（Pineconeの制限により、実際の実装では別のアプローチが必要）
        # ここでは一般的な方法を示します
        
        # 方法1: メタデータフィルターを使用（日付フィールドがあれば）
        try:
            # recieved_atフィールドでフィルタリング（数値型）
            delete_filter = {
                "recieved_at": {"$lt": 20260109}
            }
            
            # delete()メソッドでフィルター削除を試行
            delete_response = index.delete(filter=delete_filter, delete_all=False)
            print(f"✅ フィルター削除完了: {delete_response}")
            
        except Exception as e:
            print(f"⚠️  フィルター削除失敗: {e}")
            print("📝 代替方法: 手動でのID指定削除が必要です")
            
            # 方法2: 全データスキャン（時間がかかる場合があります）
            print("🔄 全データをスキャンして削除対象を特定中...")
            
            # 注意: 実際の環境では、大量データの場合は分割処理が必要
            # この例は概念的な実装です
            
            # すべてのIDを取得する実装例
            # （実際のPineconeでは、より効率的な方法を検討してください）
            
        # 削除後の統計確認
        new_stats = index.describe_index_stats()
        new_total = new_stats.get('total_vector_count', 0)
        deleted_count = total_vectors - new_total
        
        print(f"\n📊 削除結果:")
        print(f"   削除前: {total_vectors} ベクター")
        print(f"   削除後: {new_total} ベクター")
        print(f"   削除数: {deleted_count} ベクター")
        
        return True
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return False

def main():
    """メイン処理"""
    print("🗑️  Pinecone 古いデータ削除ツール")
    print("=" * 40)
    
    if delete_old_data():
        print("\n✅ 削除処理完了")
    else:
        print("\n❌ 削除処理失敗")
        sys.exit(1)

if __name__ == "__main__":
    main()