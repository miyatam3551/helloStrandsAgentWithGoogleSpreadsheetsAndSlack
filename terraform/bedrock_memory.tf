# DynamoDB Table for Episodic Memory
resource "aws_dynamodb_table" "conversation_memory" {
  name           = "${var.agent_name}-conversation-memory"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "user_id"
  range_key      = "timestamp"

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "N"
  }

  attribute {
    name = "session_id"
    type = "S"
  }

  # Global Secondary Index for session-based queries
  global_secondary_index {
    name            = "session-index"
    hash_key        = "session_id"
    range_key       = "timestamp"
    projection_type = "ALL"
  }

  # TTL to automatically delete old conversations (e.g., after 90 days)
  ttl {
    attribute_name = "expiration_time"
    enabled        = true
  }

  # Enable point-in-time recovery for data protection
  point_in_time_recovery {
    enabled = true
  }

  # Encryption at rest
  server_side_encryption {
    enabled = true
  }

  tags = {
    Name        = "${var.agent_name}-conversation-memory"
    Description = "Stores episodic memory for AI agent conversations"
  }
}

# S3 Bucket for long-term conversation archives
resource "aws_s3_bucket" "conversation_archive" {
  bucket = "${var.agent_name}-conversation-archive-${var.aws_account_id}"

  tags = {
    Name        = "${var.agent_name}-conversation-archive"
    Description = "Long-term storage for conversation history"
  }
}

# Enable versioning on archive bucket
resource "aws_s3_bucket_versioning" "conversation_archive" {
  bucket = aws_s3_bucket.conversation_archive.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Lifecycle policy to transition to cheaper storage classes
resource "aws_s3_bucket_lifecycle_configuration" "conversation_archive" {
  bucket = aws_s3_bucket.conversation_archive.id

  rule {
    id     = "archive-old-conversations"
    status = "Enabled"

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    expiration {
      days = 365
    }
  }
}

# S3 bucket encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "conversation_archive" {
  bucket = aws_s3_bucket.conversation_archive.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
