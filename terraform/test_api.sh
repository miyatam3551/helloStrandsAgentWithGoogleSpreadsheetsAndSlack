#!/usr/bin/env bash
#
# API Gateway エンドポイントをテストするスクリプト
# 使用方法: ./test_api.sh "プロンプトテキスト"
#

set -e

# スクリプトのディレクトリに移動
cd "$(dirname "$0")"

# terraform output から API エンドポイントを取得
echo "🔍 Terraform output から API エンドポイントを取得中..."
API_ENDPOINT=$(terraform output -raw api_endpoint)

if [ -z "$API_ENDPOINT" ]; then
    echo "❌ エラー: API エンドポイントが見つかりません"
    echo "terraform apply が完了していることを確認してください"
    exit 1
fi

echo "✅ API エンドポイント: ${API_ENDPOINT}/invoke"
echo ""

# 環境変数から Slack チャネル名を取得（デフォルト: general）
SLACK_TEST_CHANNEL="${SLACK_TEST_CHANNEL:-general}"

# プロンプトをコマンドライン引数から取得（デフォルト値にチャネル名を埋め込み）
PROMPT="${1:-Slack の #${SLACK_TEST_CHANNEL} チャネルに独自性にあふれる「テストメッセージ」を送信してください}"

echo "📤 リクエスト送信中..."
echo "プロンプト: ${PROMPT}"
echo ""

# API にリクエストを送信
curl -X POST "${API_ENDPOINT}/invoke" \
  -H "Content-Type: application/json" \
  -d "{\"prompt\": \"${PROMPT}\"}" \
  -w "\n\n⏱️  HTTP Status: %{http_code}\n⏱️  Total time: %{time_total}s\n" \
  -s

echo ""
echo "✅ テスト完了"
