#!/bin/bash

# 環境変数の設定
export PATH="/usr/local/bin:/usr/bin:/bin"
export LANG="en_US.UTF-8"

# 日付計算（前日の日付を取得）
YESTERDAY=$(date -d "yesterday" +%Y%m%d)

# ログファイルの設定
LOG_DIR="/opt/job-matching-api/logs"
LOG_FILE="${LOG_DIR}/daily_format_yoin_$(date +%Y%m%d).log"

# ログディレクトリの作成
mkdir -p "$LOG_DIR"

# ログ開始
echo "===========================================" >> "$LOG_FILE"
echo "Daily format_yoin job started at $(date)" >> "$LOG_FILE"
echo "Processing date: $YESTERDAY" >> "$LOG_FILE"
echo "Current user: $(whoami)" >> "$LOG_FILE"
echo "Current directory: $(pwd)" >> "$LOG_FILE"
echo "===========================================" >> "$LOG_FILE"

# プロジェクトディレクトリに移動
cd /opt/job-matching-api/app

# 仮想環境をアクティベート
source /opt/job-matching-api/venv/bin/activate

# Python環境の確認
echo "Python version: $(python --version)" >> "$LOG_FILE"
echo "Virtual environment: $VIRTUAL_ENV" >> "$LOG_FILE"

# 要員構造化フロー（with_index=true）を実行
echo "Executing: python job_matching_flow.py format_yoin start_date=$YESTERDAY end_date=$YESTERDAY limit=1000 with_index=true" >> "$LOG_FILE"

python job_matching_flow.py format_yoin start_date="$YESTERDAY" end_date="$YESTERDAY" limit=1000 with_index=true >> "$LOG_FILE" 2>&1

# 実行結果のチェック
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo "SUCCESS: Daily format_yoin (with index) job completed successfully at $(date)" >> "$LOG_FILE"
else
    echo "ERROR: Daily format_yoin (with index) job failed with exit code $EXIT_CODE at $(date)" >> "$LOG_FILE"
fi

echo "===========================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# 古いログファイルの削除（30日以上古いもの）
find "$LOG_DIR" -name "daily_format_yoin_*.log" -mtime +30 -delete