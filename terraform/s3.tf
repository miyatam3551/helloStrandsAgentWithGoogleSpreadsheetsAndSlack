resource "aws_s3_bucket" "lambda_artifacts" {
 bucket = "${var.agent_name}-lambda-artifacts"
}
