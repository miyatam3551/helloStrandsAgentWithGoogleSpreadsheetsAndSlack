# Bedrock AgentCore Memory セットアップガイド

このガイドでは、Amazon Bedrock AgentCore Memory を使用するための設定手順を説明します。

## 前提条件

- AWS アカウントと適切な権限
- Terraform がインストールされていること
- AWS CLI が設定されていること

## セットアップ手順

### 1. Bedrock Memory の作成

AWS コンソールから以下の手順で Memory を作成します:

1. **Amazon Bedrock コンソールを開く**
   - AWS マネジメントコンソールにログイン
   - Amazon Bedrock サービスに移動

2. **Memory の作成**
   - 左メニューから **Memory** を選択
   - **Create memory** ボタンをクリック
   - Memory の名前を入力（例: `hello-agent-memory`）
   - Memory の設定を行う

3. **必要な ID を取得**
   作成した Memory から以下の ID を取得します:
   - **MEM_ID**: `sample_session_memory-XXXXXXXXXXXX` の形式
   - **MEMORY_STRATEGY_ID**: `preference_builtin_XXXXXX-XXXXXXXXXX` の形式

### 2. Terraform 変数の設定

取得した ID を `terraform.tfvars` ファイルに追加します:

```hcl
# 既存の変数
aws_account_id              = "your-account-id"
param_spreadsheet_id        = "/path/to/spreadsheet/id"
param_google_credentials    = "/path/to/google/credentials"
param_slack_bot_token       = "/path/to/slack/bot/token"
param_slack_signing_secret  = "/path/to/slack/signing/secret"

# Bedrock Memory の設定（新規追加）
bedrock_memory_id           = "sample_session_memory-XXXXXXXXXXXX"
bedrock_memory_strategy_id  = "preference_builtin_XXXXXX-XXXXXXXXXX"
```

### 3. Terraform の適用

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

## アーキテクチャ

### メモリストレージ

- **OpenSearch Serverless Collection**: ベクトルデータの保存用
- **Bedrock Knowledge Base**: メモリ管理とクエリ処理

### IAM 権限

Lambda 関数には以下の権限が付与されます:

- `bedrock:Retrieve`: Memory からデータを取得
- `bedrock:RetrieveAndGenerate`: Memory を使用した生成
- `bedrock:GetKnowledgeBase`: Knowledge Base へのアクセス
- `bedrock-agent:*`: AgentCore 操作
- `aoss:APIAccessAll`: OpenSearch Serverless へのアクセス

## セッション管理

- **User ID**: Slack のユーザー ID を使用
- **Session ID**: Slack のスレッド ID（`thread_ts`）を使用
- 各スレッドが独立したセッションとして管理されます

## トラブルシューティング

### Memory が見つからない場合

1. AWS コンソールで Memory が正しく作成されているか確認
2. `MEM_ID` と `MEMORY_STRATEGY_ID` が正しいか確認
3. Lambda 関数の環境変数が正しく設定されているか確認

### 権限エラーが発生する場合

1. IAM ロールに必要な権限が付与されているか確認
2. OpenSearch Serverless のアクセスポリシーが正しいか確認
3. CloudWatch Logs でエラーログを確認

## 参考資料

- [Bedrock AgentCore SDK - Strands Integration](https://github.com/aws/bedrock-agentcore-sdk-python/tree/main/src/bedrock_agentcore/memory/integrations/strands)
- [AWS Bedrock AgentCore Samples - Terraform](https://github.com/awslabs/amazon-bedrock-agentcore-samples/tree/main/04-infrastructure-as-code/terraform/end-to-end-weather-agent)
- [Classmethod Article - Strands Agents AgentCore Memory](https://dev.classmethod.jp/articles/strands-agents-agentcore-memory-session-manager/)

## コスト見積もり

### OpenSearch Serverless
- Collection 基本料金: ~$700/月
- データストレージ: 使用量による
- リクエスト料金: 使用量による

### Bedrock
- Memory 操作: リクエストごとに課金
- Embedding モデル: トークンごとに課金

**注意**: 本番環境で使用する前に、AWS の料金計算ツールでコストを見積もることを推奨します。

## セキュリティ考慮事項

1. **データプライバシー**: ユーザーの会話履歴が Memory に保存されます
2. **アクセス制御**: IAM ポリシーで適切にアクセスを制限してください
3. **データ保持**: データ保持ポリシーに従ってデータを管理してください
4. **暗号化**: OpenSearch Serverless は AWS 管理キーで暗号化されます

## データ削除

ユーザーから削除依頼があった場合:

1. OpenSearch Serverless Collection から該当データを削除
2. または、Collection 全体を再作成

詳細は AWS ドキュメントを参照してください。
