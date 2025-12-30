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
      BEDROCK_REGION   = var.aws_region
      BEDROCK_MODEL_ID = var.bedrock_model_id
    }
  }

  # Docker イメージがビルド・プッシュされた後にデプロイ
  depends_on = [null_resource.docker_build_and_push]
}
