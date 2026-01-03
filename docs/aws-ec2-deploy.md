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
8. [Nginxの設定（オプション）](#nginxの設定オプション)
9. [SSL証明書の設定（オプション）](#ssl証明書の設定オプション)
10. [動作確認](#動作確認)
11. [トラブルシューティング](#トラブルシューティング)

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
ssh -i ~/.ssh/job-matching-key.pem ubuntu@<YOUR_EC2_PUBLIC_IP>
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
# Python 3.11のインストール
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Gitのインストール
sudo apt install -y git

# その他の必要なツール
sudo apt install -y build-essential
```

### Step 3: Python仮想環境の作成
```bash
# アプリケーション用ディレクトリの作成
sudo mkdir -p /opt/job-matching-api
sudo chown ubuntu:ubuntu /opt/job-matching-api
cd /opt/job-matching-api

# 仮想環境の作成
python3.11 -m venv venv

# 仮想環境の有効化
source venv/bin/activate
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
sudo journalctl -u job-matching-api --since "1 hour ago"
```

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
python3.11 -m venv venv
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
