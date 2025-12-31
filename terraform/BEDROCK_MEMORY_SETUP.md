# Bedrock AgentCore Memory セットアップガイド

このガイドでは、Amazon Bedrock AgentCore Memory を使用するための設定手順を説明します。

## 前提条件

- AWS アカウントと適切な権限
- Terraform がインストールされていること（v1.5 以降推奨）
- AWS CLI が設定されていること
- Python 3.8 以降（メモリ初期化スクリプト用）

## アーキテクチャ概要

このプロジェクトでは、**Terraform で Bedrock AgentCore Memory を自動作成**します。

### 主要コンポーネント

1. **aws_bedrockagentcore_memory**: エージェントの会話履歴を保存するメモリリソース
2. **null_resource + Python スクリプト**: メモリの初期化と検証
3. **Lambda 環境変数**: メモリ ID を Lambda 関数に自動注入

### セッション管理

- **User ID**: Slack のユーザー ID (`event.user`)
- **Session ID**: Slack のスレッド ID (`thread_ts`)
- 各スレッドが独立したセッションとして管理されます

## セットアップ手順

### 1. Terraform の実行

以下のコマンドで Bedrock AgentCore Memory を作成します:

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

### 2. 初期化の確認

Terraform apply 実行時に、以下の処理が自動実行されます:

1. **Memory リソースの作成**
   - イベント保持期間: 30日
   - タグ付け（Name, ManagedBy, Project）

2. **Python スクリプトによる初期化**
   - Memory の存在確認
   - 初期化ステータスの出力

### 3. Lambda 関数への環境変数設定

以下の環境変数が自動的に Lambda 関数に設定されます:

- `MEM_ID`: Terraform で作成した Memory の ID

**手動での Memory ID 設定は不要です。**

## Terraform リソース構成

### bedrock_memory.tf

```hcl
resource "aws_bedrockagentcore_memory" "memory" {
  name                  = "${replace(var.agent_name, "-", "_")}_memory"
  description           = "Memory for ${var.agent_name} to maintain conversation context"
  event_expiry_duration = 30 # Days
}
```

### 初期化スクリプト

`terraform/scripts/init-memory.py` が以下の処理を実行します:

- Memory の存在確認
- 初期化ステータスの出力
- エラーハンドリング

## IAM 権限

Lambda 関数には以下の権限が付与されます:

```json
{
  "Effect": "Allow",
  "Action": [
    "bedrock-agentcore:GetMemory",
    "bedrock-agentcore:PutMemoryItem",
    "bedrock-agentcore:DeleteMemoryItem",
    "bedrock-agentcore:ListMemories"
  ],
  "Resource": "<memory-arn>"
}
```

**変更点**: 以前の実装で使用していた OpenSearch Serverless 関連の権限は不要になりました。

## Python コードでの使用方法

`slack_event_handler.py` での使用例:

```python
from bedrock_agentcore.memory import AgentCoreMemoryConfig, AgentCoreMemorySessionManager

# Memory 設定（環境変数から MEM_ID を自動取得）
memory_config = AgentCoreMemoryConfig(
    user_id=user,
    session_id=thread_ts
)

# Session Manager を作成
session_manager = AgentCoreMemorySessionManager(config=memory_config)

# Agent を作成
agent = session_manager.create_agent(
    system_prompt=system_prompt,
    tools=[add_project, notify_slack],
    model=os.environ.get('BEDROCK_MODEL_ID')
)
```

## トラブルシューティング

### Terraform apply 時にエラーが発生する場合

**エラー例**: `Error creating Bedrock AgentCore Memory`

**対処法**:
1. AWS リージョンが Bedrock AgentCore に対応しているか確認
   - 対応リージョン: us-east-1, us-west-2, ap-northeast-1 など
2. IAM ユーザー/ロールに Bedrock AgentCore の作成権限があるか確認
   - 必要な権限: `bedrock-agentcore:CreateMemory`

### Python スクリプトの初期化エラー

**エラー例**: `✗ Error: MEMORY_ID environment variable is not set`

**対処法**:
1. Terraform の `null_resource.initialize_memory` が正しく実行されているか確認
2. `terraform apply` を再実行

### Lambda 関数でメモリが見つからない場合

**エラー例**: `Memory not found` または `AccessDeniedException`

**対処法**:
1. Lambda 関数の環境変数 `MEM_ID` が設定されているか確認
   ```bash
   aws lambda get-function-configuration --function-name hello-agent
   ```
2. IAM ロールに `bedrock-agentcore:GetMemory` 権限があるか確認
3. CloudWatch Logs でエラーログを確認

## コスト見積もり

### Bedrock AgentCore Memory

- **メモリストレージ**: イベント数に応じて課金
- **API コール**: リクエストごとに課金
- **イベント保持**: 30日間（設定値）

**OpenSearch Serverless は不要**になったため、以前の実装と比較して大幅にコストを削減できます。

**参考コスト** (2025年1月時点):
- Memory API コール: 約 $0.001/1000リクエスト
- イベントストレージ: 約 $0.25/GB/月

**注意**: 本番環境で使用する前に、AWS の料金計算ツールでコストを見積もることを推奨します。

## セキュリティ考慮事項

1. **データプライバシー**: ユーザーの会話履歴が Memory に保存されます
   - 個人情報保護法、GDPR などの規制に準拠してください
   - データ保持期間を適切に設定してください（現在: 30日）

2. **アクセス制御**: IAM ポリシーで適切にアクセスを制限してください
   - 最小権限の原則に従い、必要な権限のみを付与

3. **暗号化**: Bedrock AgentCore Memory は AWS 管理キーで暗号化されます

4. **監査**: CloudTrail で Memory へのアクセスログを記録できます

## データ削除

ユーザーから削除依頼があった場合:

### 方法1: 特定ユーザーのデータ削除

```python
import boto3

client = boto3.client('bedrock-agentcore')
client.delete_memory_item(
    memoryId=os.environ['MEM_ID'],
    userId='<user_id>',
    sessionId='<session_id>'
)
```

### 方法2: Memory 全体の削除

```bash
# Terraform で Memory を削除
terraform destroy -target=aws_bedrockagentcore_memory.memory
```

**警告**: Memory を削除すると、すべてのユーザーの会話履歴が失われます。

## 参考資料

- [Bedrock AgentCore SDK - Strands Integration](https://github.com/aws/bedrock-agentcore-sdk-python/tree/main/src/bedrock_agentcore/memory/integrations/strands)
- [AWS Bedrock AgentCore Samples - Terraform](https://github.com/awslabs/amazon-bedrock-agentcore-samples/tree/main/04-infrastructure-as-code/terraform/end-to-end-weather-agent)
- [Classmethod Article - Strands Agents AgentCore Memory](https://dev.classmethod.jp/articles/strands-agents-agentcore-memory-session-manager/)

## 変更履歴

### v2.0 (2025-12-31)
- ✅ `aws_bedrockagentcore_memory` に変更
- ✅ OpenSearch Serverless の削除（コスト削減）
- ✅ 手動 Memory 作成手順の削除
- ✅ Terraform による完全自動化
- ✅ IAM 権限の最小化

### v1.0 (初期実装)
- ❌ `aws_bedrockagent_knowledge_base` + OpenSearch Serverless
- ❌ 手動での Memory ID 設定が必要
- ❌ 過剰な IAM 権限（`bedrock-agent:*`, `aoss:APIAccessAll`）
