# AWS EC2 デプロイ手順書

このドキュメントでは、Job Matching API を AWS EC2 (Ubuntu) にデプロイする手順を説明します。

## 目次
1. [前提条件](#前提条件)
2. [EC2インスタンスの作成](#ec2インスタンスの作成)
3. [セキュリティグループの設定](#セキュリティグループの設定)
4. [EC2への接続](#ec2への接続)
5. [環境構築](#環境構築)
6. [アプリケーションのデプロイ](#アプリケーションのデプロイ)
7. [systemdサービスの設定](#systemdサービスの設定)
8. [cronジョブの設定（定期実行）](#cronジョブの設定定期実行)
9. [Nginxの設定（オプション）](#nginxの設定オプション)
10. [SSL証明書の設定（オプション）](#ssl証明書の設定オプション)
11. [セキュリティ対策](#セキュリティ対策)
12. [動作確認](#動作確認)
13. [トラブルシューティング](#トラブルシューティング)

---

## 前提条件

- AWSアカウントを所有している
- AWS CLIがインストールされている（オプション）
- SSHキーペアを作成済み、または作成する準備がある
- ローカルにGitがインストールされている

---

## EC2インスタンスの作成

### Step 1: AWSコンソールにログイン
1. [AWS Management Console](https://console.aws.amazon.com/) にアクセス
2. リージョンを選択（例: `ap-northeast-1` 東京リージョン）

### Step 2: EC2ダッシュボードに移動
1. サービス検索で「EC2」を検索してクリック
2. 「インスタンスを起動」ボタンをクリック

### Step 3: インスタンスの設定

#### 名前とタグ
```
名前: job-matching-api
```

#### AMI（Amazon Machine Image）の選択
```
Ubuntu Server 24.04 LTS (HVM), SSD Volume Type
または
Ubuntu Server 22.04 LTS (HVM), SSD Volume Type
アーキテクチャ: 64-bit (x86)
```

**注意**: 「Ubuntu Pro」ではなく通常の「Ubuntu Server」を選択してください（無料）。

#### インスタンスタイプの選択
```
t2.micro（無料利用枠対象）または t3.small（推奨）
```

#### キーペアの作成/選択
```
新しいキーペアを作成する場合:
- キーペア名: job-matching-key
- キーペアタイプ: RSA
- プライベートキーファイル形式: .pem（Mac/Linux）または .ppk（Windows PuTTY）
```

**重要**: ダウンロードした.pemファイルは安全な場所に保存してください。

#### ネットワーク設定
```
VPC: デフォルトVPC
サブネット: 任意のパブリックサブネット
パブリックIPの自動割り当て: 有効化
```

#### ストレージの設定
```
ルートボリューム: 20 GiB gp3
```

### Step 4: インスタンスを起動
「インスタンスを起動」ボタンをクリック

---

## セキュリティグループの設定

EC2インスタンスのセキュリティグループで以下のインバウンドルールを設定：

| タイプ | プロトコル | ポート範囲 | ソース | 説明 |
|--------|-----------|-----------|--------|------|
| SSH | TCP | 22 | マイIP | SSH接続用 |
| HTTP | TCP | 80 | 0.0.0.0/0 | HTTP接続用 |
| HTTPS | TCP | 443 | 0.0.0.0/0 | HTTPS接続用 |
| カスタムTCP | TCP | 8000 | 0.0.0.0/0 | FastAPI直接アクセス用 |

### AWS CLIでの設定（オプション）
```bash
# セキュリティグループの作成
aws ec2 create-security-group \
  --group-name job-matching-sg \
  --description "Security group for Job Matching API"

# ルールの追加
aws ec2 authorize-security-group-ingress \
  --group-name job-matching-sg \
  --protocol tcp \
  --port 22 \
  --cidr $(curl -s https://checkip.amazonaws.com)/32

aws ec2 authorize-security-group-ingress \
  --group-name job-matching-sg \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
  --group-name job-matching-sg \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
  --group-name job-matching-sg \
  --protocol tcp \
  --port 8000 \
  --cidr 0.0.0.0/0
```

---

## EC2への接続

### Step 1: キーファイルの権限設定（Mac/Linux）
```bash
# ダウンロードしたキーファイルの場所に移動
chmod 400 ~/Downloads/job-matching-key.pem

# キーを.sshディレクトリに移動（推奨）
mv ~/Downloads/job-matching-key.pem ~/.ssh/
```

### Step 2: SSH接続
```bash
# EC2のパブリックIPアドレスを確認してから接続
# <YOUR_EC2_PUBLIC_IP> を実際のIPアドレスに置き換え
# Ubuntuの場合、ユーザー名は「ubuntu」
ssh -i ~/.ssh/myawskey.pem ubuntu@<YOUR_EC2_PUBLIC_IP>
```

### 接続できない場合の確認事項
- セキュリティグループでポート22が開いているか
- キーファイルの権限が400になっているか
- パブリックIPアドレスが正しいか
- ユーザー名が「ubuntu」になっているか（Amazon Linuxは「ec2-user」）

---

## 環境構築

### Step 1: システムのアップデート
```bash
sudo apt update && sudo apt upgrade -y
```

### Step 2: 必要なパッケージのインストール
```bash
# Python 3.12のインストール
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev python3-pip

# Gitのインストール
sudo apt install -y git

# その他の必要なツール
sudo apt install -y build-essential
```

### Step 3: pythonコマンドのエイリアス設定
```bash
# python コマンドで python3.12 が起動するようにエイリアス設定
echo 'alias python=python3.12' >> ~/.bashrc
echo 'alias python3=python3.12' >> ~/.bashrc

# 設定を反映
source ~/.bashrc

# 確認
python --version  # Python 3.12.x と表示されればOK
```

### Step 4: Python仮想環境の作成
```bash
# アプリケーション用ディレクトリの作成
sudo mkdir -p /opt/job-matching-api
sudo chown ubuntu:ubuntu /opt/job-matching-api
cd /opt/job-matching-api

# 仮想環境の作成（エイリアスはスクリプト実行時に効かないため python3.12 を直接指定）
python3.12 -m venv venv

# 仮想環境の有効化
source venv/bin/activate

# 仮想環境内では python コマンドが使える
python --version  # Python 3.12.x
```

---

## アプリケーションのデプロイ

### Step 1: リポジトリのクローン
```bash
cd /opt/job-matching-api

# GitHubからクローン（プライベートリポジトリの場合はPersonal Access Tokenが必要）
git clone https://github.com/ykstudio626/AIJOB_lc.git app

# または、ローカルからファイルを転送
# ローカルマシンで実行:
# scp -i ~/.ssh/job-matching-key.pem -r /Users/yusukekohno/Documents/AIJOB_lc/* ubuntu@<YOUR_EC2_PUBLIC_IP>:/opt/job-matching-api/app/
```

### Step 2: 依存パッケージのインストール
```bash
cd /opt/job-matching-api/app
source ../venv/bin/activate

# pipのアップグレード
pip install --upgrade pip

# 依存パッケージのインストール
pip install -r requirements.txt
```

### Step 3: 環境変数の設定
```bash
# .envファイルの作成
cat << 'EOF' > /opt/job-matching-api/app/.env
OPENAI_API_KEY=your_openai_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_HOST=your_pinecone_index_host_here
EOF

# ファイルの権限設定
chmod 600 /opt/job-matching-api/app/.env
```

**重要**: `your_*_here` の部分を実際のAPIキーに置き換えてください。

### Step 4: 動作確認（テスト起動）
```bash
cd /opt/job-matching-api/app
source ../venv/bin/activate

# テスト起動
uvicorn main:app --host 0.0.0.0 --port 8000

# Ctrl+C で停止
```

ブラウザで `http://<YOUR_EC2_PUBLIC_IP>:8000/docs` にアクセスして動作確認。

---

## systemdサービスの設定

アプリケーションをバックグラウンドで永続的に実行するためにsystemdサービスを設定します。

### Step 1: サービスファイルの作成
```bash
sudo tee /etc/systemd/system/job-matching-api.service << 'EOF'
[Unit]
Description=Job Matching API Service
After=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/opt/job-matching-api/app
Environment="PATH=/opt/job-matching-api/venv/bin"
EnvironmentFile=/opt/job-matching-api/app/.env
ExecStart=/opt/job-matching-api/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

### Step 2: サービスの有効化と起動
```bash
# systemdの再読み込み
sudo systemctl daemon-reload

# サービスの有効化（起動時に自動起動）
sudo systemctl enable job-matching-api

# サービスの起動
sudo systemctl start job-matching-api

# ステータスの確認
sudo systemctl status job-matching-api
```

### サービス管理コマンド
```bash
# サービスの停止
sudo systemctl stop job-matching-api

# サービスの再起動
sudo systemctl restart job-matching-api

# ログの確認
sudo journalctl -u job-matching-api -f

# 直近のログを確認
sudo journalctl -u job-matching-api --since "12 hour ago"
```

---

## cronジョブの設定（定期実行）

アプリケーションの定期的な処理（例：毎朝の案件データ構造化）を自動化するためにcronジョブを設定します。

### Step 1: 自動実行用スクリプトの作成

#### 案件データ自動構造化スクリプト
```bash
# スクリプトディレクトリの作成
sudo mkdir -p /opt/job-matching-api/scripts
sudo mkdir -p /opt/job-matching-api/logs

# スクリプトファイルの作成
sudo tee /opt/job-matching-api/scripts/daily_format_anken.sh << 'EOF'
#!/bin/bash

# 環境変数の設定
export PATH="/usr/local/bin:/usr/bin:/bin"
export LANG="en_US.UTF-8"

# 日付計算（前日の日付を取得）
YESTERDAY=$(date -d "yesterday" +%Y%m%d)

# ログファイルの設定
LOG_DIR="/opt/job-matching-api/logs"
LOG_FILE="${LOG_DIR}/daily_format_anken_$(date +%Y%m%d).log"

# ログディレクトリの作成
mkdir -p "$LOG_DIR"

# ログ開始
echo "===========================================" >> "$LOG_FILE"
echo "Daily format_anken job started at $(date)" >> "$LOG_FILE"
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

# 案件構造化フローを実行
echo "Executing: python job_matching_flow.py format_anken start_date=$YESTERDAY end_date=$YESTERDAY limit=500" >> "$LOG_FILE"

python job_matching_flow.py format_anken start_date="$YESTERDAY" end_date="$YESTERDAY" limit=500 >> "$LOG_FILE" 2>&1

# 実行結果のチェック
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo "SUCCESS: Daily format_anken job completed successfully at $(date)" >> "$LOG_FILE"
else
    echo "ERROR: Daily format_anken job failed with exit code $EXIT_CODE at $(date)" >> "$LOG_FILE"
fi

echo "===========================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# 古いログファイルの削除（30日以上古いもの）
find "$LOG_DIR" -name "daily_format_anken_*.log" -mtime +30 -delete
EOF

# 実行権限の設定
sudo chmod +x /opt/job-matching-api/scripts/daily_format_anken.sh
sudo chown ubuntu:ubuntu /opt/job-matching-api/scripts/daily_format_anken.sh
sudo chown -R ubuntu:ubuntu /opt/job-matching-api/logs
```

#### 要員データ自動構造化スクリプト（オプション）
```bash
sudo tee /opt/job-matching-api/scripts/daily_format_yoin.sh << 'EOF'
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
echo "===========================================" >> "$LOG_FILE"

# プロジェクトディレクトリに移動
cd /opt/job-matching-api/app

# 仮想環境をアクティベート
source /opt/job-matching-api/venv/bin/activate

# 要員構造化フローを実行
echo "Executing: python job_matching_flow.py format_yoin start_date=$YESTERDAY end_date=$YESTERDAY limit=500" >> "$LOG_FILE"

python job_matching_flow.py format_yoin start_date="$YESTERDAY" end_date="$YESTERDAY" limit=500 >> "$LOG_FILE" 2>&1

# 実行結果のチェック
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo "SUCCESS: Daily format_yoin job completed successfully at $(date)" >> "$LOG_FILE"
else
    echo "ERROR: Daily format_yoin job failed with exit code $EXIT_CODE at $(date)" >> "$LOG_FILE"
fi

echo "===========================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# 古いログファイルの削除（30日以上古いもの）
find "$LOG_DIR" -name "daily_format_yoin_*.log" -mtime +30 -delete
EOF

sudo chmod +x /opt/job-matching-api/scripts/daily_format_yoin.sh
sudo chown ubuntu:ubuntu /opt/job-matching-api/scripts/daily_format_yoin.sh
```

#### 要員データ自動構造化+インデックス登録スクリプト（推奨）
```bash
sudo tee /opt/job-matching-api/scripts/daily_format_yoin_with_index.sh << 'EOF'
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
echo "Daily format_yoin (with index) job started at $(date)" >> "$LOG_FILE"
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
EOF

sudo chmod +x /opt/job-matching-api/scripts/daily_format_yoin_with_index.sh
sudo chown ubuntu:ubuntu /opt/job-matching-api/scripts/daily_format_yoin_with_index.sh
```

### Step 2: スクリプトのテスト実行
```bash
# 案件データ構造化スクリプトのテスト
sudo -u ubuntu /opt/job-matching-api/scripts/daily_format_anken.sh

# ログファイルの確認
tail -20 /opt/job-matching-api/logs/daily_format_anken_$(date +%Y%m%d).log
```

### Step 3: cronジョブの設定
```bash
# ubuntu ユーザーのcrontabを編集
sudo -u ubuntu crontab -e

# エディタが開いたら、以下の行を追加：

# 毎朝4:30に前日分の案件データを構造化
30 4 * * * /opt/job-matching-api/scripts/daily_format_anken.sh

# 毎朝5:30に前日分の要員データを構造化+インデックス登録（推奨）
30 5 * * * /opt/job-matching-api/scripts/daily_format_yoin_with_index.sh

# または、要員データの構造化のみの場合
# 30 5 * * * /opt/job-matching-api/scripts/daily_format_yoin.sh

# 月曜日の朝6:00にインデックス更新（週1回、オプション）
# 0 6 * * 1 /opt/job-matching-api/scripts/weekly_index_update.sh
```

### Step 4: crontabの確認
```bash
# 設定したcronジョブの確認
sudo -u ubuntu crontab -l

# cron サービスの状態確認
sudo systemctl status cron
```

### cronの時刻設定例

| 設定 | 説明 | cron表記 |
|------|------|----------|
| 毎朝4:30 | 毎日午前4時30分 | `30 4 * * *` |
| 毎時0分 | 毎時ちょうど | `0 * * * *` |
| 平日9:00 | 平日の午前9時 | `0 9 * * 1-5` |
| 月1回 | 毎月1日午前2時 | `0 2 1 * *` |
| 週1回 | 毎週日曜午前3時 | `0 3 * * 0` |

### Step 5: ログローテーション設定（オプション）
```bash
# ログローテーション設定
sudo tee /etc/logrotate.d/job-matching-api << 'EOF'
/opt/job-matching-api/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 ubuntu ubuntu
}
EOF
```

### 監視とメンテナンス

#### ログの確認
```bash
# 最新のログファイルを確認
tail -f /opt/job-matching-api/logs/daily_format_anken_$(date +%Y%m%d).log

# 過去のログファイル一覧
ls -la /opt/job-matching-api/logs/

# cronの実行ログを確認
sudo grep CRON /var/log/syslog | tail -20
```

#### トラブルシューティング
```bash
# cronサービスの再起動
sudo systemctl restart cron

# 手動でスクリプト実行してテスト
sudo -u ubuntu /opt/job-matching-api/scripts/daily_format_anken.sh

# スクリプトのデバッグ実行
bash -x /opt/job-matching-api/scripts/daily_format_anken.sh
```

#### よくある問題と対処法

1. **権限エラー**: スクリプトファイルに実行権限があることを確認
2. **パスエラー**: スクリプト内でフルパスを使用
3. **環境変数**: cronは限定的な環境変数のみ使用するため、必要な変数は明示的に設定
4. **仮想環境**: 正しいパスで仮想環境をアクティベート

---

## Nginxの設定（オプション）

本番環境ではNginxをリバースプロキシとして使用することを推奨します。

### Step 1: Nginxのインストール
```bash
sudo apt install -y nginx
```

### Step 2: Nginx設定ファイルの作成
```bash
sudo tee /etc/nginx/conf.d/job-matching-api.conf << 'EOF'
server {
    listen 80;
    server_name _;  # ドメイン名がある場合は置き換え

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }
}
EOF
```

### Step 3: Nginxの起動
```bash
# 設定のテスト
sudo nginx -t

# Nginxの有効化と起動
sudo systemctl enable nginx
sudo systemctl start nginx
```

### Step 4: FastAPIのバインドアドレスを変更
Nginxを使う場合、FastAPIは127.0.0.1にバインドします：

```bash
# サービスファイルを編集
sudo sed -i 's/--host 0.0.0.0/--host 127.0.0.1/' /etc/systemd/system/job-matching-api.service

# 再読み込みと再起動
sudo systemctl daemon-reload
sudo systemctl restart job-matching-api
```

---

## SSL証明書の設定（オプション）

Let's Encryptを使用して無料のSSL証明書を取得します。

### 前提条件
- ドメイン名を所有している
- ドメインのDNSがEC2のパブリックIPを指している

### Step 1: Certbotのインストール
```bash
sudo apt install -y certbot python3-certbot-nginx
```

### Step 2: SSL証明書の取得
```bash
# ドメイン名を置き換えて実行
sudo certbot --nginx -d your-domain.com
```

### Step 3: 自動更新の確認
```bash
# 自動更新のテスト
sudo certbot renew --dry-run
```

---

## セキュリティ対策

### 11.1 セキュリティグループの厳格化

EC2インスタンスへの不要なアクセスを防ぐため、セキュリティグループルールを最小限に制限します。

```bash
# 現在のセキュリティグループルールを確認
aws ec2 describe-security-groups --group-ids sg-xxxxx

# 不要なポートへのアクセスを削除（例：8000番ポートの全開放を削除）
aws ec2 revoke-security-group-ingress \
    --group-id sg-xxxxx \
    --protocol tcp \
    --port 8000 \
    --cidr 0.0.0.0/0

# 必要最小限のアクセスのみ許可
# SSH (22) - 管理者IPのみ
aws ec2 authorize-security-group-ingress \
    --group-id sg-xxxxx \
    --protocol tcp \
    --port 22 \
    --cidr YOUR_IP/32

# HTTP/HTTPS (80/443) - Nginx経由でのみアクセス
aws ec2 authorize-security-group-ingress \
    --group-id sg-xxxxx \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
    --group-id sg-xxxxx \
    --protocol tcp \
    --port 443 \
    --cidr 0.0.0.0/0
```

### 11.2 Fail2Banの導入

不審なアクセスパターンを検知し、自動的にIPをブロックします。

```bash
# Fail2Banのインストール
sudo apt update
sudo apt install fail2ban -y

# 設定ファイルの作成
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local

# カスタム設定
sudo tee /etc/fail2ban/jail.d/custom.conf <<EOF
[DEFAULT]
# デフォルト設定
bantime = 3600
findtime = 600
maxretry = 5

# SSH攻撃対策
[sshd]
enabled = true
port = 22
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 7200

# Nginx アクセスログ監視
[nginx-req-limit]
enabled = true
filter = nginx-req-limit
action = iptables-multiport[name=ReqLimit, port="http,https", protocol=tcp]
logpath = /var/log/nginx/access.log
findtime = 600
bantime = 7200
maxretry = 10

# 404エラー大量発生対策
[nginx-noscript]
enabled = true
port = http,https
filter = nginx-noscript
logpath = /var/log/nginx/access.log
maxretry = 6
bantime = 86400

EOF

# カスタムフィルターの作成
sudo tee /etc/fail2ban/filter.d/nginx-req-limit.conf <<EOF
[Definition]
failregex = ^<HOST> -.*"(GET|POST).*" (404|444) .*$
ignoreregex =
EOF

sudo tee /etc/fail2ban/filter.d/nginx-noscript.conf <<EOF
[Definition]
failregex = ^<HOST> -.*GET.*(\\.(php|asp|exe|pl|cgi|scgi)).*HTTP.*" (404|444) .*$
ignoreregex =
EOF

# Fail2Banの起動と有効化
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# 状態確認
sudo fail2ban-client status
sudo fail2ban-client status sshd
```

### 11.3 Nginxセキュリティ設定強化

Nginxの設定を強化し、DDoS攻撃や不正アクセスを軽減します。

```nginx
# /etc/nginx/sites-available/job-matching-api
server {
    listen 80;
    server_name your-domain.com;
    
    # セキュリティヘッダー
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # サーバー情報の隠蔽
    server_tokens off;
    
    # レート制限
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;
    
    # 大きなリクエストボディの制限
    client_max_body_size 1M;
    
    # 不正なUser-Agentのブロック
    if ($http_user_agent ~* (nmap|nikto|wikto|sf|sqlmap|bsqlbf|w3af|acunetix|havij|appscan)) {
        return 444;
    }
    
    # 管理者パスやAPIエンドポイントへの攻撃対策
    location ~ /(admin|wp-admin|phpmyadmin|adminer|manager|console) {
        return 444;
    }
    
    # APIエンドポイントにレート制限適用
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # その他のリクエスト
    location / {
        limit_req zone=api burst=5 nodelay;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 11.4 システムアップデートとパッチ管理

```bash
# 自動アップデートの設定
sudo apt install unattended-upgrades apt-listchanges -y

# 設定ファイルの編集
sudo dpkg-reconfigure -plow unattended-upgrades

# 手動でのアップデート確認（定期実行推奨）
sudo apt update && sudo apt list --upgradable

# セキュリティアップデートのみ適用
sudo unattended-upgrade --dry-run
sudo unattended-upgrade
```

### 11.5 ログ監視とアラート

```bash
# ログローテーションの設定
sudo tee /etc/logrotate.d/job-matching-api <<EOF
/opt/job-matching-api/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    copytruncate
    create 644 ubuntu ubuntu
}
EOF

# 不審なアクセスパターンの監視スクリプト
sudo tee /opt/job-matching-api/scripts/security_monitor.sh <<'EOF'
#!/bin/bash

# ログファイルパス
NGINX_LOG="/var/log/nginx/access.log"
APP_LOG="/opt/job-matching-api/logs/uvicorn.log"
SECURITY_LOG="/opt/job-matching-api/logs/security.log"

# 閾値設定
IP_REQUEST_THRESHOLD=100
ERROR_THRESHOLD=50

# 過去1時間のアクセス統計
echo "[$(date)] Security monitoring started" >> $SECURITY_LOG

# 1時間あたりのリクエスト数が多いIPを検出
awk -v threshold=$IP_REQUEST_THRESHOLD '
  $4 > (systime() - 3600) {
    ip_count[$1]++
  }
  END {
    for (ip in ip_count) {
      if (ip_count[ip] > threshold) {
        print "[ALERT] High request volume from IP:", ip, "Requests:", ip_count[ip]
      }
    }
  }' $NGINX_LOG >> $SECURITY_LOG

# 404エラーが多いIPを検出
awk -v threshold=$ERROR_THRESHOLD '
  $9 == "404" && $4 > (systime() - 3600) {
    error_count[$1]++
  }
  END {
    for (ip in error_count) {
      if (error_count[ip] > threshold) {
        print "[ALERT] High 404 error rate from IP:", ip, "Errors:", error_count[ip]
      }
    }
  }' $NGINX_LOG >> $SECURITY_LOG

# 攻撃パターンの検出
grep -E "(sql|union|select|script|alert|eval|exec)" $NGINX_LOG | tail -n 10 >> $SECURITY_LOG

echo "[$(date)] Security monitoring completed" >> $SECURITY_LOG
EOF

chmod +x /opt/job-matching-api/scripts/security_monitor.sh

# cronに追加（1時間毎実行）
echo "0 * * * * /opt/job-matching-api/scripts/security_monitor.sh" | sudo crontab -
```

### 11.6 バックアップとリカバリ

```bash
# アプリケーションとログのバックアップスクリプト
sudo tee /opt/job-matching-api/scripts/backup.sh <<'EOF'
#!/bin/bash

BACKUP_DIR="/opt/backups/job-matching-api"
DATE=$(date +%Y%m%d_%H%M%S)
APP_DIR="/opt/job-matching-api"

# バックアップディレクトリ作成
sudo mkdir -p $BACKUP_DIR

# アプリケーションファイルのバックアップ
echo "Creating application backup..."
sudo tar -czf $BACKUP_DIR/app_backup_$DATE.tar.gz \
    --exclude="$APP_DIR/logs/*" \
    --exclude="$APP_DIR/.git" \
    --exclude="$APP_DIR/__pycache__" \
    $APP_DIR

# ログファイルのバックアップ（過去7日分）
echo "Creating log backup..."
sudo tar -czf $BACKUP_DIR/logs_backup_$DATE.tar.gz \
    $APP_DIR/logs/*.log

# 古いバックアップの削除（30日以上前）
echo "Cleaning old backups..."
sudo find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR"
EOF

chmod +x /opt/job-matching-api/scripts/backup.sh

# 毎日午前2時にバックアップ実行
echo "0 2 * * * /opt/job-matching-api/scripts/backup.sh" | sudo crontab -
```

### 11.7 セキュリティ監査チェックリスト

#### 日次確認項目
- [ ] Fail2Banの状態確認: `sudo fail2ban-client status`
- [ ] 不審なログイン試行の確認: `sudo grep "Failed password" /var/log/auth.log | tail -20`
- [ ] システムリソースの確認: `top`, `df -h`, `free -m`
- [ ] アプリケーションサービスの状態: `sudo systemctl status job-matching-api`

#### 週次確認項目
- [ ] セキュリティアップデートの確認と適用
- [ ] ログファイルのローテーション確認
- [ ] バックアップファイルの整合性確認
- [ ] 新しい脆弱性情報の確認

#### 月次確認項目
- [ ] セキュリティグループルールの見直し
- [ ] 不要なポートやサービスの確認
- [ ] SSL証明書の有効期限確認
- [ ] アクセスログの分析と異常検知

### 11.8 インシデント対応手順

#### 不正アクセス検知時の対応

1. **即座の対応**
   ```bash
   # 該当IPの即座ブロック
   sudo iptables -I INPUT -s SUSPICIOUS_IP -j DROP
   
   # Fail2Banでの永続的ブロック
   sudo fail2ban-client set sshd banip SUSPICIOUS_IP
   ```

2. **ログ分析**
   ```bash
   # アクセスパターンの分析
   grep SUSPICIOUS_IP /var/log/nginx/access.log
   grep SUSPICIOUS_IP /var/log/auth.log
   grep SUSPICIOUS_IP /opt/job-matching-api/logs/uvicorn.log
   ```

3. **被害範囲の調査**
   - データベースへの不正アクセス確認
   - ファイルシステムの改ざん確認
   - 機密情報の漏洩確認

4. **報告と記録**
   - インシデントログの作成
   - 関係者への報告
   - 対策の実施記録

---

## 動作確認

### ヘルスチェック
```bash
# EC2内から
curl http://localhost:8000/health

# 外部から（Nginxなし）
curl http://<YOUR_EC2_PUBLIC_IP>:8000/health

# 外部から（Nginx経由）
curl http://<YOUR_EC2_PUBLIC_IP>/health
```

### APIドキュメントの確認
ブラウザで以下のURLにアクセス：
- Swagger UI: `http://<YOUR_EC2_PUBLIC_IP>:8000/docs`
- ReDoc: `http://<YOUR_EC2_PUBLIC_IP>:8000/redoc`

### エンドポイントのテスト
```bash
# matching_yoinエンドポイントのテスト
curl -X POST "http://<YOUR_EC2_PUBLIC_IP>:8000/matching_yoin" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Python開発者",
    "anken": "{\"案件名\": \"Webアプリ開発\", \"必須スキル\": \"Python\", \"作業場所\": \"東京\", \"単価\": \"5000円\", \"備考\": \"経験3年以上\"}"
  }'
```

---

## トラブルシューティング

### サービスが起動しない場合
```bash
# ログの確認
sudo journalctl -u job-matching-api -n 50

# 手動で起動してエラーを確認
cd /opt/job-matching-api/app
source ../venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

### ポートがブロックされている場合
```bash
# UFW（Ubuntu Firewall）の状態確認
sudo ufw status

# UFWが有効な場合、ポートを開放
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8000/tcp
sudo ufw enable
```

### 依存パッケージのエラー
```bash
# 仮想環境を再作成
cd /opt/job-matching-api
rm -rf venv
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r app/requirements.txt
```

### メモリ不足の場合
```bash
# スワップファイルの作成
sudo dd if=/dev/zero of=/swapfile bs=128M count=16
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 永続化
echo '/swapfile swap swap defaults 0 0' | sudo tee -a /etc/fstab
```

---

## 参考リンク

- [AWS EC2 ドキュメント](https://docs.aws.amazon.com/ec2/)
- [FastAPI デプロイメント](https://fastapi.tiangolo.com/deployment/)
- [Uvicorn デプロイメント](https://www.uvicorn.org/deployment/)
- [Let's Encrypt](https://letsencrypt.org/)

---

## 更新履歴

| 日付 | 内容 |
|------|------|
| 2026-01-01 | 初版作成 |
| 2026-01-12 | cronジョブの設定セクション追加 |
| 2026-01-14 | セキュリティ対策セクション追加 |
