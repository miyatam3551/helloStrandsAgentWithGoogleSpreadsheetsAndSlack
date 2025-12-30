# DynamoDB テーブル: Slack イベントの重複処理を防ぐ
# 目的: event_id を使用してイベントの重複を検出する
resource "aws_dynamodb_table" "slack_events" {
  name           = "${var.agent_name}-slack-events"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "event_id"

  attribute {
    name = "event_id"
    type = "S"
  }

  # TTL を有効化（古いイベントを自動削除）
  ttl {
    attribute_name = "expiration_time"
    enabled        = true
  }

  tags = {
    Name        = "${var.agent_name}-slack-events"
    Description = "Slack event deduplication table"
  }
}
