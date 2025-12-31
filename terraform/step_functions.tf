# Step Functions用のIAMロール
resource "aws_iam_role" "step_functions_role" {
  name = "${var.agent_name}-step-functions-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.agent_name}-step-functions-role"
  }
}

# Step FunctionsがLambda関数を実行できるようにする
resource "aws_iam_role_policy" "step_functions_lambda_invoke" {
  name = "${var.agent_name}-step-functions-lambda-invoke"
  role = aws_iam_role.step_functions_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = [
          aws_lambda_function.processor.arn
        ]
      }
    ]
  })
}

# AI処理用Lambda関数
resource "aws_lambda_function" "processor" {
  function_name = "${var.agent_name}-processor"
  role          = aws_iam_role.lambda_execution_role.arn
  timeout       = 60
  memory_size   = 512
  architectures = ["arm64"]

  # Docker コンテナイメージを使用（受付Lambda関数と同じイメージ）
  package_type = "Image"
  image_uri    = "${aws_ecr_repository.lambda_repository.repository_url}:latest"
  image_config {
    command = ["lambda_processor.handler"]
  }

  environment {
    variables = {
      BEDROCK_MODEL_ID            = var.bedrock_model_id
      PARAM_SPREADSHEET_ID        = var.param_spreadsheet_id
      PARAM_GOOGLE_CREDENTIALS    = var.param_google_credentials
      PARAM_SLACK_BOT_TOKEN       = var.param_slack_bot_token
      SLACK_SIGNING_SECRET_PARAM  = var.param_slack_signing_secret
      DYNAMODB_TABLE_NAME         = aws_dynamodb_table.slack_events.name
      CONVERSATION_MEMORY_TABLE   = aws_dynamodb_table.conversation_memory.name
      CONVERSATION_ARCHIVE_BUCKET = aws_s3_bucket.conversation_archive.id
      MEMORY_RETENTION_DAYS       = var.memory_retention_days
      MAX_CONVERSATION_HISTORY    = var.max_conversation_history
    }
  }

  depends_on = [null_resource.docker_build_and_push]
}

# Step Functionsステートマシン
resource "aws_sfn_state_machine" "slack_event_processor" {
  name     = "${var.agent_name}-event-processor"
  role_arn = aws_iam_role.step_functions_role.arn

  definition = jsonencode({
    Comment = "Slack Events API イベントを非同期処理"
    StartAt = "ProcessSlackEvent"
    States = {
      ProcessSlackEvent = {
        Type     = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = aws_lambda_function.processor.arn
          "Payload.$" = "$"
        }
        Retry = [
          {
            ErrorEquals = [
              "Lambda.ServiceException",
              "Lambda.AWSLambdaException",
              "Lambda.SdkClientException"
            ]
            IntervalSeconds = 2
            MaxAttempts     = 3
            BackoffRate     = 2.0
          }
        ]
        End = true
      }
    }
  })

  tags = {
    Name = "${var.agent_name}-event-processor"
  }
}
