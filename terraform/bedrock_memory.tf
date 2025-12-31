# Amazon Bedrock AgentCore Memory リソース
# 目的: エージェントの会話履歴とユーザーのコンテキストを保存するメモリストレージを作成

# Bedrock Memory (Knowledge Base として作成)
resource "aws_bedrockagent_knowledge_base" "agent_memory" {
  name        = "${var.agent_name}-memory"
  description = "Agent conversation memory for ${var.agent_name}"
  role_arn    = aws_iam_role.bedrock_memory_role.arn

  knowledge_base_configuration {
    type = "VECTOR"
    vector_knowledge_base_configuration {
      embedding_model_arn = "arn:aws:bedrock:${var.aws_region}::foundation-model/amazon.titan-embed-text-v1"
    }
  }

  storage_configuration {
    type = "OPENSEARCH_SERVERLESS"
    opensearch_serverless_configuration {
      collection_arn    = aws_opensearchserverless_collection.memory_collection.arn
      vector_index_name = "memory-index"
      field_mapping {
        vector_field   = "embedding"
        text_field     = "text"
        metadata_field = "metadata"
      }
    }
  }
}

# OpenSearch Serverless Collection for Memory Storage
resource "aws_opensearchserverless_collection" "memory_collection" {
  name = "${var.agent_name}-memory-collection"
  type = "VECTORSEARCH"
}

# OpenSearch Serverless Security Policy
resource "aws_opensearchserverless_security_policy" "memory_encryption" {
  name = "${var.agent_name}-memory-encryption"
  type = "encryption"
  policy = jsonencode({
    Rules = [
      {
        Resource = [
          "collection/${var.agent_name}-memory-collection"
        ]
        ResourceType = "collection"
      }
    ]
    AWSOwnedKey = true
  })
}

resource "aws_opensearchserverless_security_policy" "memory_network" {
  name = "${var.agent_name}-memory-network"
  type = "network"
  policy = jsonencode([
    {
      Rules = [
        {
          Resource = [
            "collection/${var.agent_name}-memory-collection"
          ]
          ResourceType = "collection"
        }
      ]
      AllowFromPublic = true
    }
  ])
}

# Data Access Policy for Lambda to access the collection
resource "aws_opensearchserverless_access_policy" "memory_access" {
  name = "${var.agent_name}-memory-access"
  type = "data"
  policy = jsonencode([
    {
      Rules = [
        {
          Resource = [
            "collection/${var.agent_name}-memory-collection"
          ]
          Permission = [
            "aoss:CreateCollectionItems",
            "aoss:UpdateCollectionItems",
            "aoss:DescribeCollectionItems"
          ]
          ResourceType = "collection"
        },
        {
          Resource = [
            "index/${var.agent_name}-memory-collection/*"
          ]
          Permission = [
            "aoss:CreateIndex",
            "aoss:UpdateIndex",
            "aoss:DescribeIndex",
            "aoss:ReadDocument",
            "aoss:WriteDocument"
          ]
          ResourceType = "index"
        }
      ]
      Principal = [
        aws_iam_role.lambda_execution_role.arn,
        aws_iam_role.bedrock_memory_role.arn
      ]
    }
  ])
}

# IAM Role for Bedrock Memory to access OpenSearch Serverless
resource "aws_iam_role" "bedrock_memory_role" {
  name = "${var.agent_name}-bedrock-memory-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "bedrock.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Policy for Bedrock Memory Role
resource "aws_iam_role_policy" "bedrock_memory_policy" {
  name = "${var.agent_name}-bedrock-memory-policy"
  role = aws_iam_role.bedrock_memory_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "aoss:APIAccessAll"
        ]
        Resource = aws_opensearchserverless_collection.memory_collection.arn
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel"
        ]
        Resource = "arn:aws:bedrock:${var.aws_region}::foundation-model/amazon.titan-embed-text-v1"
      }
    ]
  })
}
