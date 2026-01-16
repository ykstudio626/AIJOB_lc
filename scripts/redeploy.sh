#!/bin/bash

# EC2上での再デプロイスクリプト
# 使用方法: sudo ./redeploy.sh

set -e  # エラー時に終了

# 色付きログ出力
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 設定
SERVICE_NAME="job-matching-api"
APP_DIR="/opt/job-matching-api"
USER="ubuntu"

# 権限チェック
if [ "$EUID" -ne 0 ]; then
    log_error "このスクリプトはsudo権限で実行してください"
    exit 1
fi

log_info "=========================================="
log_info "Job Matching API 再デプロイ開始"
log_info "=========================================="

# 1. サービスの停止
log_info "サービスを停止中..."
systemctl stop $SERVICE_NAME || {
    log_warn "サービス停止に失敗しましたが、続行します"
}

# サービス状態確認
if systemctl is-active --quiet $SERVICE_NAME; then
    log_error "サービスの停止に失敗しました"
    exit 1
else
    log_info "✅ サービス停止完了"
fi

# 2. アプリケーションディレクトリへ移動
log_info "アプリケーションディレクトリへ移動: $APP_DIR"
if [ ! -d "$APP_DIR" ]; then
    log_error "アプリケーションディレクトリが存在しません: $APP_DIR"
    exit 1
fi

cd $APP_DIR

# 3. Gitの状態確認とクリーンアップ
log_info "Git状態をクリーンアップ中..."
sudo -u $USER git status || {
    log_error "Gitリポジトリではありません"
    exit 1
}

# 未コミットの変更があれば警告
if ! sudo -u $USER git diff --quiet; then
    log_warn "⚠️ 未コミットの変更があります。stashします..."
    sudo -u $USER git stash
fi

# 4. Git pull実行
log_info "最新コードを取得中 (git pull origin main)..."
sudo -u $USER git pull origin main || {
    log_error "Git pull に失敗しました"
    exit 1
}

log_info "✅ コード更新完了"

# 5. 権限の修正
log_info "ファイル権限を修正中..."
chown -R $USER:$USER $APP_DIR
chmod +x $APP_DIR/scripts/*.sh 2>/dev/null || true

# 6. Python依存関係のアップデート（requirements.txtがある場合）
if [ -f "requirements.txt" ]; then
    log_info "Python依存関係を確認中..."
    sudo -u $USER /usr/bin/python3 -m pip install -r requirements.txt --user --no-warn-script-location
fi

# 7. サービスの再起動
log_info "サービスを再起動中..."
systemctl start $SERVICE_NAME || {
    log_error "サービス起動に失敗しました"
    log_error "ログを確認してください: sudo journalctl -u $SERVICE_NAME -n 20"
    exit 1
}

# サービスの有効化
systemctl enable $SERVICE_NAME

# 8. 起動待機
log_info "サービス起動を待機中..."
sleep 5

# 9. 状態確認
log_info "サービス状態を確認中..."
if systemctl is-active --quiet $SERVICE_NAME; then
    log_info "✅ サービス正常起動"
    systemctl status $SERVICE_NAME --no-pager -l
else
    log_error "❌ サービス起動失敗"
    log_error "詳細ログ:"
    journalctl -u $SERVICE_NAME --no-pager -n 10
    exit 1
fi

# 10. ヘルスチェック
log_info "ヘルスチェック実行中..."
for i in {1..6}; do
    log_info "ヘルスチェック試行 $i/6..."
    if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
        log_info "✅ アプリケーション正常稼働中"
        break
    elif [ $i -eq 6 ]; then
        log_warn "⚠️ ヘルスチェック失敗 - アプリケーションが応答しません"
        log_warn "サービスログ:"
        journalctl -u $SERVICE_NAME --no-pager -n 10
    else
        sleep 10
    fi
done

log_info "=========================================="
log_info "✅ 再デプロイ完了"
log_info "アプリケーション URL: http://localhost:8000"
log_info "ログ確認: sudo journalctl -u $SERVICE_NAME -f"
log_info "=========================================="