# 統合テスト実装完了

## 実装内容

このプルリクエストでは、以下の統合テストを実装しました：

### 1. 重複イベント検出テスト (同じevent_idの重複リクエスト)

**実装ファイル:** `tests/integration/test_event_deduplication.py::TestDuplicateEventDetection`

#### test_duplicate_event_id_rejected
- **目的:** 同じ event_id を持つ重複リクエストが正しく検出・拒否されることを確認
- **検証内容:**
  - 最初のリクエストが正常に処理される
  - 2回目の同じ event_id のリクエストは重複として検出される（200 OK は返すが処理はスキップ）
  - DynamoDB テーブルに event_id が1つだけ保存される
  - Step Functions の実行が1回だけトリガーされる

#### test_different_event_ids_both_processed
- **目的:** 異なる event_id のリクエストが両方とも正しく処理されることを確認
- **検証内容:**
  - 2つの異なる event_id のリクエストが両方処理される
  - DynamoDB テーブルに2つの event_id が保存される
  - Step Functions の実行が2回トリガーされる

### 2. Step Functions 実行確認テスト

**実装ファイル:** `tests/integration/test_event_deduplication.py::TestStepFunctionsExecution`

#### test_step_functions_triggered_on_valid_request
- **目的:** 有効なリクエストで Step Functions が正しく起動することを確認
- **検証内容:**
  - Lambda 関数が即座に 200 OK を返す（非同期処理）
  - Step Functions の実行が開始される
  - 新しい実行 ARN が生成される

#### test_step_functions_execution_completes_successfully
- **目的:** Step Functions の実行が正常に完了することを確認
- **検証内容:**
  - 実行が SUCCEEDED ステータスに到達する
  - Processor Lambda が呼び出される
  - エラーが発生しない（最大60秒待機）

## ディレクトリ構造

```
tests/
├── __init__.py                          # テストパッケージ初期化
├── conftest.py                          # pytest設定とフィクスチャ
├── requirements-test.txt                # テスト依存関係
├── .env.example                         # 環境変数の例
├── README.md                            # テスト実行手順の詳細ドキュメント
└── integration/
    ├── __init__.py
    ├── test_event_deduplication.py      # メインテストファイル
    └── test_utils.py                    # テストユーティリティ
```

## テストユーティリティ

`tests/integration/test_utils.py` には以下のヘルパー関数を実装：

- **generate_slack_signature**: Slack の署名を生成（HMAC-SHA256）
- **create_slack_event_payload**: Slack Events API のペイロードを作成
- **create_api_gateway_event**: API Gateway イベントを作成（署名付き）

## 追加機能

### 1. Terraform Outputs の追加
`terraform/outputs.tf` に以下のアウトプットを追加：
- `dynamodb_table_name`: DynamoDB テーブル名
- `state_machine_arn`: Step Functions ステートマシン ARN
- `processor_lambda_function_name`: プロセッサ Lambda 関数名

### 2. 環境変数セットアップスクリプト
`setup_test_env.sh`: Terraform のアウトプットから環境変数を自動抽出し、`tests/.env` ファイルを生成

### 3. pytest 設定
`pytest.ini`: テストの検出パターン、マーカー、ログ設定を定義

## テストの実行方法

### 前提条件
1. AWS リソースが Terraform でデプロイされていること
2. AWS 認証情報が設定されていること

### クイックスタート

```bash
# 1. テスト依存関係のインストール
pip install -r tests/requirements-test.txt

# 2. 環境変数のセットアップ
./setup_test_env.sh

# 3. テストの実行
pytest tests/integration/ -v
```

### 個別テストの実行

```bash
# 重複検出テストのみ
pytest tests/integration/test_event_deduplication.py::TestDuplicateEventDetection -v

# Step Functions 実行テストのみ
pytest tests/integration/test_event_deduplication.py::TestStepFunctionsExecution -v
```

## テスト設計の特徴

### 1. 実際の AWS リソースを使用
- モックではなく、実際の AWS サービス（DynamoDB、Step Functions、Lambda）を使用
- 本番環境に近い統合テストを実現

### 2. 署名検証のサポート
- Slack の署名を正しく生成してテスト
- セキュリティ機能も含めて検証

### 3. タイムアウトとリトライ
- Step Functions の完了を待つ際に適切なタイムアウトを設定
- 非同期処理の完了を確実に検証

### 4. クリーンアップ不要
- DynamoDB の TTL 機能により、古いテストデータは自動削除される
- テスト後の手動クリーンアップは不要

## CI/CD 統合

GitHub Actions などの CI/CD パイプラインでの実行例：

```yaml
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

- name: Setup test environment
  run: ./setup_test_env.sh

- name: Run integration tests
  run: pytest tests/integration/ -v
```

## 注意事項

1. **AWS 料金**: 統合テストの実行には AWS の使用料金が発生します（わずかですが）
2. **実行時間**: Step Functions の完了を待つテストは最大60秒かかる場合があります
3. **並列実行**: 同時に複数のテストを実行すると、event_id の競合が発生する可能性があります
4. **認証情報**: AWS 認証情報が正しく設定されていることを確認してください

## 関連ファイル

- `tests/README.md`: 詳細なテスト実行手順とトラブルシューティング
- `tests/.env.example`: 環境変数の設定例
- `pytest.ini`: pytest の設定ファイル
- `setup_test_env.sh`: 環境変数自動セットアップスクリプト
