output "lambda_function_name" {
 value = aws_lambda_function.agent.function_name
 description = "Lambda 関数名 (受付 Lambda)"
}

output "slack_events_endpoint" {
 value = "${aws_apigatewayv2_stage.default.invoke_url}slack/events"
 description = "Slack Events API の Request URL として設定するエンドポイント"
}

output "dynamodb_table_name" {
 value = aws_dynamodb_table.slack_events.name
 description = "DynamoDB テーブル名 (イベント重複検出用)"
}

output "state_machine_arn" {
 value = aws_sfn_state_machine.slack_event_processor.arn
 description = "Step Functions ステートマシン ARN"
}

output "processor_lambda_function_name" {
 value = aws_lambda_function.processor.function_name
 description = "Lambda 関数名 (プロセッサ Lambda)"
}

