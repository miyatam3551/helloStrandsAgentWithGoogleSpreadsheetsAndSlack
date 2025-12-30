# ECR リポジトリの作成
# 目的: Lambda 関数の Docker イメージを保存するための ECR リポジトリを作成する
resource "aws_ecr_repository" "lambda_repository" {
  name                 = "${var.agent_name}-lambda"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  force_delete = true  # Terraform destroy 時にイメージがあっても削除可能

  tags = {
    Name = "${var.agent_name}-lambda-repository"
  }
}

# ECR リポジトリのライフサイクルポリシー
# 目的: 古いイメージを自動削除してストレージコストを削減
resource "aws_ecr_lifecycle_policy" "lambda_repository_policy" {
  repository = aws_ecr_repository.lambda_repository.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "最新の10イメージのみ保持"
        selection = {
          tagStatus     = "any"
          countType     = "imageCountMoreThan"
          countNumber   = 10
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# null_resource: Docker イメージのビルドとプッシュ
# 目的: Dockerfile からイメージをビルドし、ECR にプッシュする
resource "null_resource" "docker_build_and_push" {
  triggers = {
    # Dockerfile か requirements.txt が変更されたら再ビルド
    dockerfile_hash    = filemd5("${path.module}/lambda_code/Dockerfile")
    requirements_hash  = filemd5("${path.module}/lambda_code/src/requirements.txt")
    # Lambda 関数コードが変更されたら再ビルド
    lambda_code_hash   = sha256(join("", [
      for f in fileset("${path.module}/lambda_code/src", "**/*.py") :
      filesha256("${path.module}/lambda_code/src/${f}")
    ]))
  }

  provisioner "local-exec" {
    command = <<EOT
      # ECR にログイン
      aws ecr get-login-password --region ${var.aws_region} | \
        docker login --username AWS --password-stdin ${aws_ecr_repository.lambda_repository.repository_url}

      # Docker イメージをビルド（arm64 アーキテクチャ用）
      docker buildx build --platform linux/arm64 \
        -t ${aws_ecr_repository.lambda_repository.repository_url}:latest \
        -f ${path.module}/lambda_code/Dockerfile \
        ${path.module}/lambda_code

      # ECR にプッシュ
      docker push ${aws_ecr_repository.lambda_repository.repository_url}:latest
    EOT
  }

  depends_on = [aws_ecr_repository.lambda_repository]
}
