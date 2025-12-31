# ============================================================================
# Amazon Bedrock AgentCore Memory
# ============================================================================
# 目的: エージェントの会話履歴とユーザーのコンテキストを保存するメモリを作成
# 参考: https://github.com/awslabs/amazon-bedrock-agentcore-samples/tree/main/04-infrastructure-as-code/terraform/end-to-end-weather-agent

data "aws_region" "current" {}

# ============================================================================
# Memory - For Persistent Conversation Context
# ============================================================================

resource "aws_bedrockagentcore_memory" "memory" {
  name                  = "${replace(var.agent_name, "-", "_")}_memory"
  description           = "Memory for ${var.agent_name} to maintain conversation context"
  event_expiry_duration = 30 # Days

  tags = {
    Name        = "${var.agent_name}-memory"
    ManagedBy   = "Terraform"
    Project     = "HelloStrandsAgent"
  }
}

# ============================================================================
# Memory Initialization - Populate Memory with Initial Context
# ============================================================================

# Initialize memory after it is created
resource "null_resource" "initialize_memory" {
  # Trigger re-initialization if memory ID changes
  triggers = {
    memory_id = aws_bedrockagentcore_memory.memory.id
    region    = data.aws_region.current.id
  }

  # Execute Python script to initialize memory
  provisioner "local-exec" {
    command     = "python3 ${path.module}/scripts/init-memory.py"
    working_dir = path.module

    environment = {
      MEMORY_ID  = aws_bedrockagentcore_memory.memory.id
      AWS_REGION = data.aws_region.current.id
    }
  }

  # Ensure memory exists before initialization
  depends_on = [
    aws_bedrockagentcore_memory.memory
  ]
}

# ============================================================================
# Outputs
# ============================================================================

output "memory_id" {
  description = "Bedrock AgentCore Memory ID"
  value       = aws_bedrockagentcore_memory.memory.id
}

output "memory_arn" {
  description = "Bedrock AgentCore Memory ARN"
  value       = aws_bedrockagentcore_memory.memory.arn
}

output "memory_initialization_status" {
  description = "Status of memory initialization"
  value       = "Memory initialized successfully"
  depends_on  = [null_resource.initialize_memory]
}
