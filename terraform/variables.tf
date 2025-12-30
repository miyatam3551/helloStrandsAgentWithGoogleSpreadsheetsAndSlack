variable "aws_region" {
 description = "AWS リージョン"
 type        = string
 default     = "ap-northeast-1"
}

variable "aws_account_id" {
 description = "AWS アカウント ID"
 type        = string
}

variable "agent_name" {
 description = "エージェント名"
 type        = string
 default     = "hello-agent"
}

variable "bedrock_model_id" {
 description = "Bedrock モデル ID"
 type        = string
 default     = "jp.anthropic.claude-sonnet-4-5-20250929-v1:0"
}

variable "param_spreadsheet_id" {
 description = "Parameter Store パス: Spreadsheet ID"
 type        = string
 sensitive   = true
}

variable "param_google_credentials" {
 description = "Parameter Store パス: Google 認証情報"
 type        = string
 sensitive   = true
}

variable "param_slack_bot_token" {
 description = "Parameter Store パス: Slack Bot Token"
 type        = string
 sensitive   = true
}

variable "param_slack_signing_secret" {
 description = "Parameter Store パス: Slack Signing Secret"
 type        = string
 sensitive   = true
}
