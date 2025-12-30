# Hello Strands Agent with Google Spreadsheets and Slack

## 📖 このプロジェクトについて

このプロジェクトは、**AI エージェントが Google Spreadsheets や Slack を自動操作できる**サンプルアプリケーションです。

自然言語で「プロジェクトを Google Sheets に追加して」「Slack に通知して」と指示すると、AI が自動的に操作を実行します。

### 💡 なぜこのプロジェクトを作ったのか？

**従来の課題:**
- Slack や Google Sheets の操作には、それぞれの API を理解し、コードを書く必要がありました
- 複数のツールを連携させるには、複雑な統合処理が必要でした

**このプロジェクトで実現できること:**
- **自然言語での操作**: 「プロジェクトを追加して」と言うだけで AI が適切なツールを選択
- **複数ツールの自動連携**: AI が Google Sheets と Slack を組み合わせて使用
- **拡張性**: 新しいツールを追加するだけで、AI が自動的に使い方を学習

### 🎯 想定される利用シーン

- **プロジェクト管理の自動化**: 「新しいプロジェクトを Sheets に追加して、チームに Slack 通知」
- **レポート作成**: 「今日のタスクを Sheets から取得して、サマリーを Slack に投稿」
- **通知の自動化**: 「重要な変更があったら Slack に通知」

---

## 🏗️ アーキテクチャ

```
┌─────────────┐
│   クライアント  │  ← HTTP POST でプロンプト送信
│  (curl/App) │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│   API Gateway       │  ← HTTP エンドポイント提供
│  (AWS)              │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────────────────┐
│  Lambda Function (Docker)       │
│  ┌───────────────────────────┐  │
│  │  Strands Agent            │  │  ← AI エージェント
│  │  - add_project ツール     │  │
│  │  - notify_slack ツール    │  │
│  └───────┬───────────────────┘  │
│          │                      │
│          ▼                      │
│  ┌───────────────┐              │
│  │  AWS Bedrock  │              │  ← Claude Sonnet 4.5
│  └───────────────┘              │
└─────────┬───────────────────────┘
          │
          ├──────────────┐
          │              │
          ▼              ▼
  ┌──────────────┐  ┌──────────┐
  │Google Sheets │  │  Slack   │
  └──────────────┘  └──────────┘
```

---

## 🔧 使用技術とその選定理由

### なぜ Strands Agent なのか？

**Strands** は、AI エージェントにツールを簡単に渡せるフレームワークです。

- **✅ 利点**: Python 関数を `@tool` デコレータで装飾するだけでツールになる
- **✅ AI が自動判断**: どのツールをいつ使うか AI が決定
- **✅ シンプル**: コード量が少なく、初学者でも理解しやすい

### なぜ AWS Lambda (Docker) なのか？

**サーバーレスアーキテクチャ**を採用しています。

- **✅ コスト削減**: 使った分だけ課金（アイドル時は無料）
- **✅ スケーラビリティ**: 自動でスケールアウト
- **✅ 運用不要**: サーバー管理が不要
- **✅ Docker コンテナ**: 依存ライブラリを含めてデプロイ可能

### なぜ AWS Bedrock なのか？

**AWS Bedrock** は、Claude などの AI モデルを API 経由で利用できるサービスです。

- **✅ API キー不要**: AWS の権限管理で安全
- **✅ 高速**: AWS 内部ネットワークで低レイテンシ
- **✅ エンタープライズ対応**: セキュリティとコンプライアンス準拠

### なぜ Terraform なのか？

**Infrastructure as Code (IaC)** を実現します。

- **✅ 再現性**: 同じ構成を何度でも再現可能
- **✅ バージョン管理**: インフラの変更履歴を Git で管理
- **✅ チーム開発**: 複数人でインフラを共同管理
- **✅ 宣言的**: 「何を作るか」を記述（手順ではなく）

### なぜ S3 Backend なのか？

Terraform の**状態ファイル (tfstate)** を S3 に保存します。

- **✅ チーム共有**: 複数人で同じ状態を参照
- **✅ ロック機能**: 同時実行を防止
- **✅ 永続化**: ローカルファイルの紛失を防止
- **✅ バージョン管理**: 状態の履歴を保持

---

## 📋 前提条件

### 1. mise のインストール

**なぜ必要？**
- Terraform、AWS CLI、Python、uv などの開発ツールを**一括管理**できる
- プロジェクトごとに異なるバージョンを自動で切り替え
- `.mise.toml` に定義されたツールを `mise install` だけでインストール

**mise のインストール方法**

```bash
# macOS
curl https://mise.run | sh

# または Homebrew
brew install mise

# シェルの設定（nushell の場合）
echo 'mise activate nu | save --append ~/.config/nushell/config.nu' | nu
```

**プロジェクトのツールをインストール**

```bash
cd helloStrandsAgentWithGoogleSpreadsheetsAndSlack
mise install
```

これで以下のツールが自動的にインストールされます：
- Python 3.14
- uv 0.9.20
- Terraform 1.14.3
- AWS CLI 2.32.25

**参考リンク:**
- [mise 公式サイト](https://mise.jdx.dev/)

> **💡 mise の利点**
> - 複数プロジェクト間でツールのバージョン競合を回避
> - `.mise.toml` でバージョンを一元管理
> - チーム全体で同じ環境を再現可能

### 2. Orbstack または Docker Desktop

**なぜ必要？**
- Lambda 関数を **Docker コンテナイメージ** としてビルドするため
- Terraform が `docker build` と `docker push` を実行

**Orbstack のインストール方法 (macOS)**

```bash
brew install orbstack
```

> **💡 Orbstack vs Docker Desktop**
> - Orbstack: 軽量・高速、macOS 専用
> - Docker Desktop: クロスプラットフォーム、機能豊富

**参考リンク:**
- [Orbstack 公式サイト](https://orbstack.dev/download)
- [Docker Desktop 公式サイト](https://www.docker.com/products/docker-desktop)

### 3. AWS アカウント

**なぜ必要？**
- Lambda、API Gateway、Bedrock などの AWS サービスを利用

**必要な権限:**
- IAM、Lambda、ECR、API Gateway、S3、Bedrock へのフルアクセス

### 4. AWS CLI の設定

**なぜ必要？**
- Terraform が AWS API を呼び出すため
- Docker イメージを ECR にプッシュするため

> **💡 AWS CLI は mise で既にインストール済み**
> - `mise install` で AWS CLI 2.32.25 がインストールされています
> - ここでは認証情報の設定のみ行います

#### AWS SSO を使用した認証

**初回設定（SSO 未設定の場合）:**

```bash
aws configure sso
```

**設定項目:**
- SSO start URL: 組織の AWS SSO ポータル URL
- SSO Region: SSO が設定されているリージョン
- Default region name: `ap-northeast-1`（東京リージョン）
- Default output format: `json`
- CLI profile name: 任意のプロファイル名（例: `default` または `your-org`）

**ログイン:**

```bash
aws sso login
```

> **💡 AWS SSO のメリット**
> - 一時的な認証情報でセキュリティ向上
> - アクセスキーの管理が不要
> - 複数アカウントへの切り替えが容易
> - MFA（多要素認証）との統合

### 5. 認証情報の準備

**なぜ必要？**
- Lambda 関数が実行時に Google Sheets や Slack にアクセスするための認証情報が必要
- これらの認証情報は後のステップで Parameter Store に暗号化して保存します

**準備する認証情報:**
1. Google サービスアカウント認証情報（JSON ファイル）
2. Slack Bot Token
3. Spreadsheet ID

#### 5-1. Google サービスアカウント認証情報の準備

**Google Cloud Console で サービスアカウントを作成:**

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. プロジェクトを選択（または新規作成）
3. 「IAM と管理」→「サービス アカウント」→「サービス アカウントを作成」
4. サービスアカウント名を入力（例: `sheets-slack-agent`）
5. 「キーを作成」→「JSON」を選択してダウンロード
6. ダウンロードした JSON ファイルを `credentials/service-account-key.json` に配置

**Google Sheets API を有効化:**

1. [Google Cloud Console](https://console.cloud.google.com/) → 「API とサービス」
2. 「ライブラリ」→「Google Sheets API」を検索
3. 「有効にする」をクリック

**スプレッドシートへのアクセス権を付与:**

1. スプレッドシートを開く
2. 「共有」をクリック
3. サービスアカウントのメールアドレス（`xxx@xxx.iam.gserviceaccount.com`）を追加
4. 「編集者」権限を付与

#### 5-2. Slack Bot Token の取得

1. [Slack API](https://api.slack.com/apps) にアクセス
2. 「Create New App」→「From scratch」
3. アプリ名とワークスペースを選択
4. 「OAuth & Permissions」→「Scopes」で以下を追加：
   - `chat:write`
   - `chat:write.public`
5. 「Install to Workspace」をクリック
6. 表示される「Bot User OAuth Token」（`xoxb-` で始まる）をコピー

#### 5-3. Spreadsheet ID の確認

スプレッドシートの URL から取得します：

```
https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit
                                      ^^^^^^^^^^^^^^
                                      この部分が ID
```

---

## 🚀 クイックスタートガイド

### 1. リポジトリのクローン

```bash
git clone https://github.com/miyatam3551/helloStrandsAgentWithGoogleSpreadsheetsAndSlack.git
cd helloStrandsAgentWithGoogleSpreadsheetsAndSlack
```

### 2. 開発ツールのインストール

```bash
mise install
```

**このコマンドで何がインストールされるか？**
- Python 3.14
- uv 0.9.20（Python パッケージマネージャ）
- Terraform 1.14.3（インフラ構築ツール）
- AWS CLI 2.32.25（AWS 操作ツール）

**確認方法:**
```bash
mise list
```

**出力例:**
```
python   3.14      ~/.local/share/mise/installs/python/3.14
uv       0.9.20    ~/.local/share/mise/installs/uv/0.9.20
terraform 1.14.3   ~/.local/share/mise/installs/terraform/1.14.3
aws      2.32.25   ~/.local/share/mise/installs/aws/2.32.25
```

### 3. 環境変数の設定

#### 3-1. .env ファイルのコピー

```bash
cp .env.example .env
```

**なぜこのステップが必要？**
- `.env.example` ファイルは**テンプレート**（Git にコミット）
- 実際の `.env` ファイルには**機密情報**（Parameter Store のパス名など）を含むため `.gitignore` で除外
- これにより、機密情報を誤って公開するリスクを回避

#### 3-2. .env の編集

```bash
vim .env
```

以下の値を**あなたの環境に合わせて**設定します：

```bash
# ============================================
# Terraform 変数
# ============================================
# TF_VAR_ プレフィックスにより Terraform が自動認識します
# これらの値は Lambda の環境変数として自動設定されます

# AWS アカウント ID（aws sts get-caller-identity --query Account --output text で取得）
TF_VAR_aws_account_id="123456789012"

# Parameter Store のパス名
# Lambda 実行時に Parameter Store からシークレットを取得する際のパスとして使用されます
TF_VAR_param_spreadsheet_id="/your-prefix/spreadsheet-id"
TF_VAR_param_google_credentials="/your-prefix/google-credentials"
TF_VAR_param_slack_bot_token="/your-prefix/slack-bot-token"
```

**設定項目の説明:**
- `TF_VAR_aws_account_id`: あなたの AWS アカウント ID（[確認方法](#aws-account-id-の確認方法)）
- `TF_VAR_param_*`: Parameter Store のパス名（Lambda 実行時にシークレットを取得する際に使用）
- プレフィックス（例: `/your-prefix/`）は推測されにくい、アプリケーション固有の名前を使用

**AWS Account ID の確認方法:**
```bash
aws sts get-caller-identity --query Account --output text
```

> **💡 .env ファイル一元管理の利点**
> - すべての設定を `.env` ファイル一つで管理（`terraform.tfvars` は不要）
> - `TF_VAR_` プレフィックスにより Terraform が自動認識
> - Parameter Store のパス名を一箇所で管理し、同期ミスを防止
> - 機密情報を `.gitignore` で保護

### 4. Parameter Store への認証情報の登録

**なぜこのステップが必要？**
- Lambda 関数が実行時に Google Sheets や Slack にアクセスするには、認証情報が必要
- `.env` ファイルで設定したパス名を使って、Parameter Store に暗号化して保存します
- **重要**: このステップは `.env` ファイルを作成した後に実行してください

**前提条件:**
- [前提条件 → 5. 認証情報の準備](#5-認証情報の準備) で以下を準備済みであること：
  - `credentials/service-account-key.json` （Google サービスアカウント認証情報）
  - Slack Bot Token （`xoxb-` で始まるトークン）
  - Spreadsheet ID

#### 4-1. Parameter Store への保存コマンド

**`.env` ファイルで設定した環境変数を使用してコマンドを実行します:**

**nushell の場合:**
```bash
# Google サービスアカウント認証情報を保存
(aws ssm put-parameter
  --name $env.TF_VAR_param_google_credentials
  --value (cat credentials/service-account-key.json)
  --type "SecureString"
  --overwrite)

# Slack Bot Token を保存
(aws ssm put-parameter
  --name $env.TF_VAR_param_slack_bot_token
  --value "xoxb-your-slack-bot-token-here"
  --type "SecureString"
  --overwrite)

# Spreadsheet ID を保存
(aws ssm put-parameter
  --name $env.TF_VAR_param_spreadsheet_id
  --value "your-spreadsheet-id-here"
  --type "SecureString"
  --overwrite)
```

**bash の場合:**

```bash
# Google サービスアカウント認証情報を保存
aws ssm put-parameter \
  --name "$TF_VAR_param_google_credentials" \
  --value "$(cat credentials/service-account-key.json)" \
  --type "SecureString" \
  --overwrite

# Slack Bot Token を保存
aws ssm put-parameter \
  --name "$TF_VAR_param_slack_bot_token" \
  --value "xoxb-your-slack-bot-token-here" \
  --type "SecureString" \
  --overwrite

# Spreadsheet ID を保存
aws ssm put-parameter \
  --name "$TF_VAR_param_spreadsheet_id" \
  --value "your-spreadsheet-id-here" \
  --type "SecureString" \
  --overwrite
```

#### 4-2. 保存の確認

```bash
# 保存されたパラメータの一覧を確認
aws ssm describe-parameters --filters "Key=Name,Values=/your-prefix/"

# 特定のパラメータの値を確認（復号化して表示）
aws ssm get-parameter --name "/your-prefix/spreadsheet-id" --with-decryption --query "Parameter.Value" --output text
```

> **💡 Parameter Store のセキュリティ**
> - `SecureString` タイプで暗号化保存（AWS KMS を使用）
> - IAM ロールによるアクセス制御
> - 値の変更履歴を保持
> - `--overwrite` オプションで既存値を更新可能

> **⚠️ 注意事項**
> - `credentials/service-account-key.json` は `.gitignore` に追加されているため、Git にコミットされません
> - Slack Bot Token は絶対に Git にコミットしないでください
> - Parameter Store のパス名（プレフィックス）は推測されにくいものを使用してください

### 5. Terraform Backend の設定

#### 5-1. backend.tf のコピー

```bash
cd terraform
cp backend.tf.example backend.tf
```

**なぜこのステップが必要？**
- `backend.tf.example` は**テンプレート**（Git にコミット）
- 実際の `backend.tf` には**S3バケット名**を含むため `.gitignore` で除外
- これにより、バケット名を誤って公開するリスクを回避

> **💡 terraform.tfvars は不要**
> - すべての変数は `.env` ファイルで `TF_VAR_*` として管理
> - `terraform.tfvars` ファイルは作成する必要がありません

#### 5-2. backend.tf の編集

```bash
vim backend.tf
```

以下の `YOUR_BUCKET_NAME` を**実際の S3 バケット名**に置き換えます：

```hcl
terraform {
  backend "s3" {
    bucket         = "my-terraform-state-bucket-12345"  # ← あなたのバケット名
    key            = "helloStrandsAgentWithGoogleSpreadsheetsAndSlack/terraform.tfstate"
    region         = "ap-northeast-1"
    use_lockfile   = true
  }
}
```

**なぜ S3 バケットが必要？**
- Terraform の**状態ファイル**を保存する場所
- チームで共有したり、状態を永続化するため
- **重要**: バケット名は全世界でユニークである必要があります

**バケットの作成方法:**

```bash
aws s3 mb s3://my-terraform-state-bucket-12345 --region ap-northeast-1
```

### 6. Terraform の実行

#### 6-1. 初期化

```bash
terraform init
```

**なぜ init が必要？**
- Terraform プラグイン（AWS Provider など）をダウンロード
- Backend（S3）の初期化
- 依存関係の解決

**このステップで行われること:**
- `.terraform/` ディレクトリが作成される
- S3 バケットに接続して状態ファイルを確認

#### 6-2. プランの確認

```bash
terraform plan
```

**なぜ plan を実行するのか？**
- **実際に作成される前に**、何が作られるかプレビューできる
- コストやリソースの確認
- エラーの事前検出

**確認すべきポイント:**
- 作成されるリソース数（`Plan: X to add, 0 to change, 0 to destroy`）
- Lambda 関数、API Gateway、ECR リポジトリなどが含まれているか

#### 6-3. インフラの構築

```bash
terraform apply
```

**なぜ apply が必要？**
- 実際に AWS リソースを作成
- Docker イメージをビルドして ECR にプッシュ
- Lambda 関数をデプロイ

**このステップで行われること:**
1. Docker イメージのビルド（数分かかります）
2. ECR へのプッシュ
3. Lambda 関数の作成
4. API Gateway の作成
5. IAM ロールの作成

**実行時間:** 初回は **5〜10分** 程度かかります

**確認メッセージ:**
```
Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value: yes  # ← "yes" と入力
```

### 7. デプロイの確認

#### 7-1. API エンドポイントの取得

```bash
terraform output api_endpoint
```

**出力例:**
```
https://xxxxx.execute-api.ap-northeast-1.amazonaws.com
```

#### 7-2. 動作確認

```bash
curl -X POST https://xxxxx.execute-api.ap-northeast-1.amazonaws.com/invoke \
  -H "Content-Type: application/json" \
  -d '{"prompt": "こんにちは！"}'
```

**期待されるレスポンス:**
```json
{
  "message": "こんにちは！何かお手伝いできることはありますか？"
}
```

**なぜこのテストが重要？**
- API Gateway → Lambda → Bedrock の全経路が正常に動作していることを確認
- 問題があれば、どこで失敗しているか切り分けられる

#### 7-3. テストスクリプトの使用

**なぜテストスクリプトを使うのか？**
- `terraform output` を自動的に取得するため、エンドポイント URL をコピー＆ペーストする手間が不要
- 毎回同じコマンドを入力する必要がなく、効率的にテストできる
- レスポンス時間や HTTP ステータスコードも自動表示

**基本的な使い方:**

```bash
# デフォルトのプロンプトでテスト
./test_api.sh
```

**カスタムプロンプトでテスト:**

```bash
# Slack への通知をテスト
./test_api.sh "Slackに「デプロイ完了」というメッセージを送信してください"

# Google Spreadsheet への追加をテスト
./test_api.sh "プロジェクト名「新機能開発」をスプレッドシートに追加してください"

# 複数ツールの連携をテスト
./test_api.sh "新しいプロジェクト「API改善」をシートに追加して、Slackに通知してください"
```

**出力例:**

```bash
🔍 Terraform output から API エンドポイントを取得中...
✅ API エンドポイント: https://xxxxx.execute-api.ap-northeast-1.amazonaws.com/invoke

📤 リクエスト送信中...
プロンプト: Slackに「テストメッセージ」を送信してください

{"message":"Slackにメッセージを送信しました！"}

⏱️  HTTP Status: 200
⏱️  Total time: 2.451s

✅ テスト完了
```

**スクリプトの特徴:**
- ✅ エンドポイント自動取得: `terraform output` から自動的に取得
- ✅ エラーハンドリング: terraform が未実行の場合はエラーメッセージを表示
- ✅ パフォーマンス測定: レスポンス時間を自動計測
- ✅ 使いやすさ: 引数を省略すればデフォルトプロンプトで実行

---

## 🐛 トラブルシューティング

### API リクエストが 500 エラーを返す

**デバッグ方法:**

```bash
# Lambda のログを確認
aws logs tail /aws/lambda/hello-agent --follow
```

**よくある原因:**
- 環境変数の設定ミス
- Bedrock モデル ID の間違い
- Google Sheets / Slack の認証情報が未設定


## 🧹 クリーンアップ

リソースを削除してコストを節約：

```bash
cd terraform
terraform destroy
```

**なぜ destroy が重要？**
- 使用していない AWS リソースは課金が続く
- 特に ECR イメージや Lambda 関数は削除しないとコストが発生

---

## 📖 学習リソース

### Strands について
- [Strands 公式ドキュメント](https://github.com/strands-ai/strands)

### AWS Bedrock について
- [AWS Bedrock 公式ドキュメント](https://docs.aws.amazon.com/bedrock/)
- [Claude on Bedrock](https://docs.anthropic.com/claude/docs/amazon-bedrock)

### Terraform について
- [Terraform 公式チュートリアル](https://learn.hashicorp.com/terraform)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)

### AI エージェントについて
- [LangChain ドキュメント](https://python.langchain.com/docs/get_started/introduction)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)

---

## 🤝 コントリビューション

Issue や Pull Request をお待ちしています！

## 📄 ライセンス

MIT License
