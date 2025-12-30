# Integration Tests

このディレクトリには、以下の機能の統合テストが含まれています：

## テスト内容

### 1. 重複イベント検出テスト (`test_event_deduplication.py`)

#### TestDuplicateEventDetection
- **test_duplicate_event_id_rejected**: 同じ event_id の重複リクエストが正しく検出され、拒否されることを確認
  - 最初のリクエストが処理される
  - 2回目の同じ event_id のリクエストは重複として検出される (200 OK は返すが処理はスキップ)
  - DynamoDB テーブルに event_id が1つだけ保存される
  - Step Functions の実行が1回だけトリガーされる

- **test_different_event_ids_both_processed**: 異なる event_id のリクエストが両方とも処理されることを確認
  - 2つの異なる event_id のリクエストが両方処理される
  - DynamoDB テーブルに2つの event_id が保存される
  - Step Functions の実行が2回トリガーされる

### 2. Step Functions 実行確認テスト (`test_event_deduplication.py`)

#### TestStepFunctionsExecution
- **test_step_functions_triggered_on_valid_request**: 有効なリクエストで Step Functions が起動することを確認
  - Lambda 関数が即座に 200 OK を返す
  - Step Functions の実行が開始される
  - 実行 ARN がログに記録される

- **test_step_functions_execution_completes_successfully**: Step Functions の実行が正常に完了することを確認
  - 実行が SUCCEEDED ステータスに到達する
  - Processor Lambda が呼び出される
  - エラーが発生しない

## セットアップ

### 1. テスト依存関係のインストール

```bash
pip install -r tests/requirements-test.txt
```

### 2. AWS リソースのデプロイ

テストを実行する前に、Terraform でインフラをデプロイしてください：

```bash
cd terraform
terraform init
terraform apply
```

### 3. 環境変数の設定

テストは以下の環境変数を必要とします：

```bash
# DynamoDB テーブル名
export DYNAMODB_TABLE_NAME=$(cd terraform && terraform output -raw dynamodb_table_name)

# Step Functions ステートマシン ARN
export STATE_MACHINE_ARN=$(cd terraform && terraform output -raw state_machine_arn)

# Lambda 関数名
export LAMBDA_FUNCTION_NAME=$(cd terraform && terraform output -raw lambda_function_name)

# AWS リージョン（オプション、デフォルト: ap-northeast-1）
export AWS_REGION=ap-northeast-1
```

または、`.env` ファイルを作成：

```bash
# tests/.env
DYNAMODB_TABLE_NAME=hello-agent-slack-events
STATE_MACHINE_ARN=arn:aws:states:ap-northeast-1:123456789012:stateMachine:hello-agent-event-processor
LAMBDA_FUNCTION_NAME=hello-agent
AWS_REGION=ap-northeast-1
```

### 4. AWS 認証

AWS CLI が設定されていることを確認してください：

```bash
aws sts get-caller-identity
```

## テストの実行

### 全テストを実行

```bash
# プロジェクトルートから
pytest tests/integration/ -v
```

### 特定のテストクラスを実行

```bash
# 重複検出テストのみ
pytest tests/integration/test_event_deduplication.py::TestDuplicateEventDetection -v

# Step Functions 実行テストのみ
pytest tests/integration/test_event_deduplication.py::TestStepFunctionsExecution -v
```

### 特定のテストメソッドを実行

```bash
# 重複リクエストテストのみ
pytest tests/integration/test_event_deduplication.py::TestDuplicateEventDetection::test_duplicate_event_id_rejected -v
```

### 詳細な出力付きで実行

```bash
pytest tests/integration/ -v -s
```

## テストのアーキテクチャ

### テストフロー

```
┌─────────────────────┐
│  Integration Test   │
└──────────┬──────────┘
           │
           │ 1. Lambda.invoke()
           ▼
┌─────────────────────┐
│  Lambda (agent)     │  ← 署名検証、重複チェック
│  - 署名検証         │
│  - DynamoDB チェック│
│  - Step Functions   │
│    起動             │
└──────────┬──────────┘
           │
           │ 2. StartExecution
           ▼
┌─────────────────────┐
│  Step Functions     │  ← 非同期処理オーケストレーション
└──────────┬──────────┘
           │
           │ 3. Lambda.invoke()
           ▼
┌─────────────────────┐
│  Lambda (processor) │  ← AI 処理
└─────────────────────┘
```

### テストユーティリティ (`test_utils.py`)

- **generate_slack_signature**: Slack 署名の生成（HMAC-SHA256）
- **create_slack_event_payload**: Slack Events API のペイロード作成
- **create_api_gateway_event**: API Gateway イベントの作成

## 注意事項

### テスト実行時の注意

1. **AWS リソースが必要**: これらは統合テストであり、実際の AWS リソース（DynamoDB、Step Functions、Lambda）が必要です
2. **AWS 料金**: テスト実行には AWS の使用料金が発生します（わずかですが）
3. **実行時間**: Step Functions の完了を待つテストは最大60秒かかる場合があります
4. **並列実行**: 同時に複数のテストを実行すると、event_id の競合が発生する可能性があります

### CI/CD での実行

GitHub Actions などの CI/CD パイプラインで実行する場合：

1. AWS 認証情報を設定（IAM ロールや OIDC を推奨）
2. Terraform でインフラをデプロイ
3. 環境変数を設定
4. テストを実行

```yaml
# .github/workflows/integration-tests.yml の例
- name: Setup AWS credentials
  uses: aws-actions/configure-aws-credentials@v2
  with:
    role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
    aws-region: ap-northeast-1

- name: Deploy infrastructure
  run: |
    cd terraform
    terraform init
    terraform apply -auto-approve

- name: Run integration tests
  env:
    DYNAMODB_TABLE_NAME: ${{ steps.terraform.outputs.dynamodb_table_name }}
    STATE_MACHINE_ARN: ${{ steps.terraform.outputs.state_machine_arn }}
    LAMBDA_FUNCTION_NAME: ${{ steps.terraform.outputs.lambda_function_name }}
  run: |
    pytest tests/integration/ -v
```

## トラブルシューティング

### "AWS resources not configured" エラー

環境変数が設定されていません。上記のセットアップ手順を確認してください。

### "No new Step Functions execution found" エラー

- Step Functions の起動に時間がかかっている可能性があります（`time.sleep` の値を増やす）
- Lambda 関数のログを確認して、エラーが発生していないか確認してください

```bash
aws logs tail /aws/lambda/hello-agent --follow
```

### "Execution did not complete within 60 seconds" エラー

- Processor Lambda が長時間実行されている可能性があります
- Lambda のタイムアウト設定を確認してください
- CloudWatch Logs でエラーを確認してください

### DynamoDB の項目が見つからない

- DynamoDB への書き込みに遅延がある可能性があります
- `time.sleep` の値を増やしてください
- DynamoDB コンソールで手動で確認してください

## 参考リンク

- [pytest ドキュメント](https://docs.pytest.org/)
- [boto3 ドキュメント](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [AWS Step Functions テスト](https://docs.aws.amazon.com/step-functions/latest/dg/sfn-local.html)
