#!/bin/bash

# シンプル再デプロイスクリプト (EC2上で実行)
# 使用方法: sudo ./simple_redeploy.sh

echo "🚀 再デプロイ開始..."

# サービス停止
echo "🛑 サービス停止中..."
sudo systemctl stop job-matching-api

# コード更新
echo "📦 コード更新中..."
cd /opt/job-matching-api
sudo -u ubuntu git pull origin main

# サービス再起動
echo "🔄 サービス再起動中..."
sudo systemctl start job-matching-api
sudo systemctl enable job-matching-api

# 状態確認
echo "📊 状態確認中..."
sleep 3
sudo systemctl status job-matching-api --no-pager

echo "✅ 再デプロイ完了!"
echo "🌐 URL: http://localhost:8000"