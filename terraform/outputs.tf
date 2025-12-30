output "lambda_function_name" {
 value = aws_lambda_function.agent.function_name
}
output "api_endpoint" {
 value = aws_apigatewayv2_stage.default.invoke_url
}

