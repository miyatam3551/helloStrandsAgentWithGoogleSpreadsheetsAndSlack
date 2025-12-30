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
