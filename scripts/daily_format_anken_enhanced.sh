#!/bin/bash
set -e  # エラー時に停止
set -x  # 実行コマンドを表示

echo "DEBUG: Script started at $(date)"

# 環境変数の設定
export PATH="/usr/local/bin:/usr/bin:/bin"
export LANG="en_US.UTF-8"

echo "DEBUG: Environment variables set"

# 日付計算（前日の日付を取得）
YESTERDAY=$(date -d "yesterday" +%Y%m%d 2>/dev/null || date -v-1d +%Y%m%d)

echo "DEBUG: Yesterday date calculated: $YESTERDAY"

# ログファイルの設定
LOG_DIR="/opt/job-matching-api/logs"
LOG_FILE="${LOG_DIR}/daily_format_anken_$(date +%Y%m%d).log"

echo "DEBUG: Log directory: $LOG_DIR"
echo "DEBUG: Log file: $LOG_FILE"

# ログディレクトリの作成
echo "DEBUG: Creating log directory..."
mkdir -p "$LOG_DIR" || {
    echo "ERROR: Failed to create log directory $LOG_DIR"
    exit 1
}

echo "DEBUG: Log directory created successfully"

# ログ開始
echo "DEBUG: Starting to write to log file..."
{
    echo "==========================================="
    echo "Daily format_anken job started at $(date)"
    echo "Processing date: $YESTERDAY"
    echo "Current user: $(whoami)"
    echo "Current directory: $(pwd)"
    echo "==========================================="
} >> "$LOG_FILE" 2>&1 || {
    echo "ERROR: Failed to write to log file $LOG_FILE"
    echo "ERROR: Current directory: $(pwd)"
    echo "ERROR: User: $(whoami)"
    echo "ERROR: Log directory permissions: $(ls -ld $LOG_DIR)"
    exit 1
}

echo "DEBUG: Log file written successfully"

# プロジェクトディレクトリの存在確認と移動
PROJECT_DIR="/opt/job-matching-api/app"
echo "DEBUG: Checking project directory: $PROJECT_DIR"

if [ ! -d "$PROJECT_DIR" ]; then
    echo "ERROR: Project directory $PROJECT_DIR does not exist"
    echo "Available directories:"
    ls -la /opt/ 2>/dev/null || echo "Cannot access /opt/"
    exit 1
fi

echo "DEBUG: Moving to project directory..."
cd "$PROJECT_DIR" || {
    echo "ERROR: Failed to change to directory $PROJECT_DIR"
    exit 1
}

echo "DEBUG: Successfully moved to $(pwd)"

# 仮想環境の存在確認とアクティベート
VENV_PATH="/opt/job-matching-api/venv"
echo "DEBUG: Checking virtual environment: $VENV_PATH"

if [ ! -d "$VENV_PATH" ]; then
    echo "ERROR: Virtual environment $VENV_PATH does not exist"
    echo "Available directories:"
    ls -la /opt/job-matching-api/ 2>/dev/null || echo "Cannot access /opt/job-matching-api/"
    exit 1
fi

echo "DEBUG: Activating virtual environment..."
source "$VENV_PATH/bin/activate" || {
    echo "ERROR: Failed to activate virtual environment"
    exit 1
}

echo "DEBUG: Virtual environment activated successfully"

# Python環境の確認
echo "DEBUG: Checking Python environment..."
{
    echo "Python version: $(python --version)"
    echo "Python path: $(which python)"
    echo "Virtual environment: $VIRTUAL_ENV"
    echo "Current working directory: $(pwd)"
    echo "Directory contents: $(ls -la)"
} >> "$LOG_FILE" 2>&1

echo "DEBUG: Python environment check completed"

# 案件構造化フローを実行
COMMAND="python job_matching_flow.py format_anken start_date=$YESTERDAY end_date=$YESTERDAY limit=500"
echo "DEBUG: Preparing to execute: $COMMAND"

# job_matching_flow.pyの存在確認
if [ ! -f "job_matching_flow.py" ]; then
    echo "ERROR: job_matching_flow.py not found in $(pwd)"
    echo "Available files:"
    ls -la >> "$LOG_FILE" 2>&1
    exit 1
fi

echo "DEBUG: job_matching_flow.py found, executing command..."

{
    echo "Executing: $COMMAND"
    echo "Execution started at: $(date)"
} >> "$LOG_FILE" 2>&1

# 実際の実行
python job_matching_flow.py format_anken start_date="$YESTERDAY" end_date="$YESTERDAY" limit=500 >> "$LOG_FILE" 2>&1

# 実行結果のチェック
EXIT_CODE=$?
echo "DEBUG: Command completed with exit code: $EXIT_CODE"

{
    echo "Execution completed at: $(date)"
    echo "Exit code: $EXIT_CODE"
} >> "$LOG_FILE" 2>&1
if [ $EXIT_CODE -eq 0 ]; then
    echo "SUCCESS: Daily format_anken job completed successfully at $(date)" >> "$LOG_FILE"
else
    echo "ERROR: Daily format_anken job failed with exit code $EXIT_CODE at $(date)" >> "$LOG_FILE"
fi

echo "===========================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# 古いログファイルの削除（30日以上古いもの）
find "$LOG_DIR" -name "daily_format_anken_*.log" -mtime +30 -delete

# 実行結果をメール通知したい場合（オプション）
# if [ $EXIT_CODE -ne 0 ]; then
#     echo "Daily format_anken job failed" | mail -s "Job Matching API Error" admin@example.com
# fi