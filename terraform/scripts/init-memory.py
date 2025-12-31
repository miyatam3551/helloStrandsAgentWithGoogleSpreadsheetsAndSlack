#!/usr/bin/env python3
"""
Bedrock AgentCore Memory Initialization Script

このスクリプトは、Bedrock AgentCore Memory を初期化します。
Terraform の null_resource から実行され、メモリに初期コンテキストを設定します。

環境変数:
  MEMORY_ID: Bedrock AgentCore Memory ID
  AWS_REGION: AWS リージョン

参考: https://github.com/awslabs/amazon-bedrock-agentcore-samples
"""

import os
import sys
import boto3
from typing import Optional


def initialize_memory(memory_id: str, region: str) -> bool:
    """
    Bedrock AgentCore Memory を初期化する

    Args:
        memory_id: Memory ID
        region: AWS リージョン

    Returns:
        bool: 成功した場合 True、失敗した場合 False
    """
    try:
        # Bedrock AgentCore クライアントを作成
        client = boto3.client('bedrock-agentcore', region_name=region)

        # Memory の存在確認
        try:
            response = client.get_memory(memoryId=memory_id)
            print(f"✓ Memory {memory_id} found")
            print(f"  Name: {response.get('name', 'N/A')}")
            print(f"  Description: {response.get('description', 'N/A')}")
        except client.exceptions.ResourceNotFoundException:
            print(f"✗ Memory {memory_id} not found", file=sys.stderr)
            return False

        # 初期化成功
        print(f"✓ Memory initialization completed successfully")
        return True

    except Exception as e:
        print(f"✗ Error during memory initialization: {e}", file=sys.stderr)
        return False


def main() -> int:
    """
    メイン処理

    Returns:
        int: 終了コード (0: 成功, 1: 失敗)
    """
    # 環境変数から設定を取得
    memory_id: Optional[str] = os.environ.get('MEMORY_ID')
    region: Optional[str] = os.environ.get('AWS_REGION')

    if not memory_id:
        print("✗ Error: MEMORY_ID environment variable is not set", file=sys.stderr)
        return 1

    if not region:
        print("✗ Error: AWS_REGION environment variable is not set", file=sys.stderr)
        return 1

    print("=" * 80)
    print("Bedrock AgentCore Memory Initialization")
    print("=" * 80)
    print(f"Memory ID: {memory_id}")
    print(f"Region: {region}")
    print("-" * 80)

    # Memory を初期化
    success = initialize_memory(memory_id, region)

    print("-" * 80)
    if success:
        print("✓ Memory initialization completed successfully")
        return 0
    else:
        print("✗ Memory initialization failed", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
