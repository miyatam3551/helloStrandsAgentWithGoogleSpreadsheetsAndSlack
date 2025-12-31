# ============================================================================
# Amazon Bedrock AgentCore Memory
# ============================================================================
# 目的: エージェントの会話履歴とユーザーのコンテキストを保存するメモリを作成
# 参考: https://github.com/awslabs/amazon-bedrock-agentcore-samples/tree/main/04-infrastructure-as-code/terraform/end-to-end-weather-agent
# 参考: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/bedrockagentcore_memory_strategy

# ============================================================================
# Memory - For Persistent Conversation Context
# ============================================================================

resource "aws_bedrockagentcore_memory" "memory" {
  name                  = "${replace(var.agent_name, "-", "_")}_memory"
  event_expiry_duration = 90 # Days
}

resource "aws_bedrockagentcore_memory_strategy" "user_pref" {
  name        = "user_preference_strategy_${replace(var.agent_name, "-", "_")}"
  memory_id   = aws_bedrockagentcore_memory.memory.id
  type        = "USER_PREFERENCE"
  description = "User preference tracking strategy"
  namespaces  = ["/strategies/{memoryStrategyId}/actors/{actorId}"]
}
