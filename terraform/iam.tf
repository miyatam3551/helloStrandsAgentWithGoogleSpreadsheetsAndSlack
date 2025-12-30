# Lambda関数用のIAMロールとポリシーを定義
resource "aws_iam_role" "lambda_execution_role" {
 name = "${var.agent_name}-lambda-role"

 assume_role_policy = jsonencode({
   Version = "2012-10-17"
   Statement = [
     {
       Action = "sts:AssumeRole"
       Effect = "Allow"
       Principal = {
         Service = "lambda.amazonaws.com"
       }
     }
   ]
 })
}

# Lambdaの基本的な実行権限を付与
resource "aws_iam_role_policy_attachment" "lambda_basic" {
 policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
 role       = aws_iam_role.lambda_execution_role.name
}

# Bedrockへのアクセス権限を付与
resource "aws_iam_role_policy" "bedrock_access" {
 name = "${var.agent_name}-bedrock-access"
 role = aws_iam_role.lambda_execution_role.id

 policy = jsonencode({
   Version = "2012-10-17"
   Statement = [
     {
       Effect = "Allow"
       Action = [
         "bedrock:InvokeModel",
         "bedrock:InvokeModelWithResponseStream"
       ]
       Resource = [
         "arn:aws:bedrock:*::foundation-model/*",
         "arn:aws:bedrock:*:${var.aws_account_id}:inference-profile/*"
       ]
     }
   ]
 })
}

# SSMパラメーターストアへのアクセス権限を付与
resource "aws_iam_role_policy" "lambda_ssm_access" {
 name = "${var.agent_name}-ssm-access"
 role = aws_iam_role.lambda_execution_role.id

 policy = jsonencode({
   Version = "2012-10-17"
   Statement = [
     {
       Effect = "Allow"
       Action = [
         "ssm:GetParameter",
         "ssm:GetParameters"
       ]
       Resource = [
         "arn:aws:ssm:${var.aws_region}:*:parameter${var.param_spreadsheet_id}",
         "arn:aws:ssm:${var.aws_region}:*:parameter${var.param_google_credentials}",
         "arn:aws:ssm:${var.aws_region}:*:parameter${var.param_slack_bot_token}",
         "arn:aws:ssm:${var.aws_region}:*:parameter${var.param_slack_signing_secret}"
       ]
     }
   ]
 })
}

# DynamoDB へのアクセス権限を付与（イベント重複検出用）
resource "aws_iam_role_policy" "lambda_dynamodb_access" {
 name = "${var.agent_name}-dynamodb-access"
 role = aws_iam_role.lambda_execution_role.id

 policy = jsonencode({
   Version = "2012-10-17"
   Statement = [
     {
       Effect = "Allow"
       Action = [
         "dynamodb:GetItem",
         "dynamodb:PutItem"
       ]
       Resource = "arn:aws:dynamodb:${var.aws_region}:${var.aws_account_id}:table/${var.agent_name}-slack-events"
     }
   ]
 })
}
