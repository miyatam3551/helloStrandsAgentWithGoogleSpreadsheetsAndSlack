# Lambda 関数（Docker コンテナイメージ版）
# 目的: ECR の Docker イメージから Lambda 関数を作成する
resource "aws_lambda_function" "agent" {
  function_name = var.agent_name
  role          = aws_iam_role.lambda_execution_role.arn
  timeout       = 60
  memory_size   = 512
  architectures = ["arm64"]

  # Docker コンテナイメージを使用
  package_type = "Image"
  image_uri    = "${aws_ecr_repository.lambda_repository.repository_url}:latest"

  environment {
    variables = {
      BEDROCK_MODEL_ID            = var.bedrock_model_id
      PARAM_SPREADSHEET_ID        = var.param_spreadsheet_id
      PARAM_GOOGLE_CREDENTIALS    = var.param_google_credentials
      PARAM_SLACK_BOT_TOKEN       = var.param_slack_bot_token
      SLACK_SIGNING_SECRET_PARAM  = var.param_slack_signing_secret
      DYNAMODB_TABLE_NAME         = aws_dynamodb_table.slack_events.name
      STATE_MACHINE_ARN           = aws_sfn_state_machine.slack_event_processor.arn
    }
  }

  # Docker イメージがビルド・プッシュされた後にデプロイ
  depends_on = [null_resource.docker_build_and_push]
}
