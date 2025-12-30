# HTTPプロトコルのAPI Gateway を作成
resource "aws_apigatewayv2_api" "agent_api" {
 name          = "${var.agent_name}-api"
 protocol_type = "HTTP"
}

# Lambda関数をAPI Gatewayに統合
resource "aws_apigatewayv2_integration" "lambda" {
 api_id           = aws_apigatewayv2_api.agent_api.id
 integration_type = "AWS_PROXY"
 integration_uri  = aws_lambda_function.agent.invoke_arn
}

# Slack Events API用のルートを作成
resource "aws_apigatewayv2_route" "slack_events" {
 api_id    = aws_apigatewayv2_api.agent_api.id
 route_key = "POST /slack/events"
 target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

# デフォルトステージを作成
resource "aws_apigatewayv2_stage" "default" {
 api_id      = aws_apigatewayv2_api.agent_api.id
 name        = "$default"
 auto_deploy = true
}

# Lambda関数にAPI Gatewayからの呼び出しを許可
resource "aws_lambda_permission" "api_gateway" {
 statement_id  = "AllowAPIGatewayInvoke"
 action        = "lambda:InvokeFunction"
 function_name = aws_lambda_function.agent.function_name
 principal     = "apigateway.amazonaws.com"
 source_arn    = "${aws_apigatewayv2_api.agent_api.execution_arn}/*/*"
}
