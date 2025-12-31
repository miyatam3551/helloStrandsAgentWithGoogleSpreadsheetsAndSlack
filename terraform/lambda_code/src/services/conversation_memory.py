"""
エピソード記憶サービス（Amazon Bedrock Agent用）
ユーザー固有の会話履歴を保存・取得する
"""
import os
import time
import json
from typing import List, Dict, Optional
import boto3
from decimal import Decimal

# DynamoDB クライアント
dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'ap-northeast-1'))
s3_client = boto3.client('s3', region_name=os.environ.get('AWS_REGION', 'ap-northeast-1'))

# 設定
MEMORY_TABLE_NAME = os.environ.get('CONVERSATION_MEMORY_TABLE')
ARCHIVE_BUCKET = os.environ.get('CONVERSATION_ARCHIVE_BUCKET')
RETENTION_DAYS = int(os.environ.get('MEMORY_RETENTION_DAYS', 90))
MAX_HISTORY = int(os.environ.get('MAX_CONVERSATION_HISTORY', 10))


class ConversationMemory:
    """AI エージェントの会話のエピソード記憶を管理"""

    def __init__(self, user_id: str, session_id: Optional[str] = None):
        """
        特定ユーザーの会話記憶を初期化

        Args:
            user_id: ユーザーの一意識別子（例: Slack ユーザー ID）
            session_id: 会話をグループ化するためのセッション識別子（オプション）
        """
        self.user_id = user_id
        self.session_id = session_id or f"session_{int(time.time())}"
        self.table = dynamodb.Table(MEMORY_TABLE_NAME) if MEMORY_TABLE_NAME else None

    def save_message(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        メッセージを会話記憶に保存

        Args:
            role: メッセージの役割（'user' または 'assistant'）
            content: メッセージ内容
            metadata: オプションのメタデータ（例: channel, thread_ts）

        Returns:
            成功した場合 True、失敗した場合 False
        """
        if not self.table:
            print("警告: 会話記憶テーブルが設定されていません")
            return False

        try:
            timestamp = Decimal(str(time.time()))
            expiration_time = int(time.time()) + (RETENTION_DAYS * 86400)

            item = {
                'user_id': self.user_id,
                'timestamp': timestamp,
                'session_id': self.session_id,
                'role': role,
                'content': content,
                'expiration_time': expiration_time,
                'metadata': metadata or {}
            }

            self.table.put_item(Item=item)
            return True

        except Exception as e:
            print(f"メッセージ保存エラー: {e}")
            return False

    def get_conversation_history(
        self,
        limit: Optional[int] = None,
        session_specific: bool = True
    ) -> List[Dict]:
        """
        ユーザーの会話履歴を取得

        Args:
            limit: 取得する最大メッセージ数（デフォルト: MAX_HISTORY）
            session_specific: True の場合、現在のセッションのメッセージのみ取得

        Returns:
            時系列順の会話メッセージリスト
        """
        if not self.table:
            print("警告: 会話記憶テーブルが設定されていません")
            return []

        try:
            limit = limit or MAX_HISTORY

            if session_specific:
                # GSI を使用してセッション ID でクエリ
                response = self.table.query(
                    IndexName='session-index',
                    KeyConditionExpression='session_id = :sid',
                    ExpressionAttributeValues={
                        ':sid': self.session_id
                    },
                    ScanIndexForward=False,  # 最新のものから取得
                    Limit=limit
                )
            else:
                # ユーザー ID（パーティションキー）でクエリ
                response = self.table.query(
                    KeyConditionExpression='user_id = :uid',
                    ExpressionAttributeValues={
                        ':uid': self.user_id
                    },
                    ScanIndexForward=False,  # 最新のものから取得
                    Limit=limit
                )

            items = response.get('Items', [])

            # Decimal を float に変換し、時系列順に並べ替え
            messages = []
            for item in reversed(items):
                messages.append({
                    'role': item['role'],
                    'content': item['content'],
                    'timestamp': float(item['timestamp']),
                    'metadata': item.get('metadata', {})
                })

            return messages

        except Exception as e:
            print(f"会話履歴取得エラー: {e}")
            return []

    def get_context_window(self) -> str:
        """
        AI のコンテキスト用にフォーマットされた会話履歴を取得

        Returns:
            最近の会話履歴のフォーマットされた文字列
        """
        history = self.get_conversation_history()

        if not history:
            return ""

        context_lines = ["過去の会話:"]
        for msg in history:
            role = "ユーザー" if msg['role'] == 'user' else "アシスタント"
            context_lines.append(f"{role}: {msg['content']}")

        return "\n".join(context_lines)

    def archive_session(self) -> bool:
        """
        現在のセッションを S3 に長期保存のためアーカイブ

        Returns:
            成功した場合 True、失敗した場合 False
        """
        if not ARCHIVE_BUCKET:
            print("警告: アーカイブバケットが設定されていません")
            return False

        try:
            history = self.get_conversation_history(limit=1000, session_specific=True)

            if not history:
                return True

            # アーカイブオブジェクトを作成
            archive_data = {
                'user_id': self.user_id,
                'session_id': self.session_id,
                'archived_at': int(time.time()),
                'messages': history
            }

            # S3 に保存
            key = f"archives/{self.user_id}/{self.session_id}.json"
            s3_client.put_object(
                Bucket=ARCHIVE_BUCKET,
                Key=key,
                Body=json.dumps(archive_data, ensure_ascii=False),
                ContentType='application/json'
            )

            print(f"セッション {self.session_id} を S3 にアーカイブしました: {key}")
            return True

        except Exception as e:
            print(f"セッションアーカイブエラー: {e}")
            return False

    def clear_session(self) -> bool:
        """
        現在のセッションのすべてのメッセージをクリア

        Returns:
            成功した場合 True、失敗した場合 False
        """
        if not self.table:
            return False

        try:
            # クリア前にアーカイブ
            self.archive_session()

            # セッション内のすべてのアイテムをクエリ
            response = self.table.query(
                IndexName='session-index',
                KeyConditionExpression='session_id = :sid',
                ExpressionAttributeValues={
                    ':sid': self.session_id
                }
            )

            # 各アイテムを削除
            with self.table.batch_writer() as batch:
                for item in response.get('Items', []):
                    batch.delete_item(
                        Key={
                            'user_id': item['user_id'],
                            'timestamp': item['timestamp']
                        }
                    )

            print(f"セッション {self.session_id} をクリアしました")
            return True

        except Exception as e:
            print(f"セッションクリアエラー: {e}")
            return False


def get_memory_for_user(user_id: str, session_id: Optional[str] = None) -> ConversationMemory:
    """
    ConversationMemory インスタンスを作成するファクトリ関数

    Args:
        user_id: ユーザーの一意識別子（例: Slack ユーザー ID）
        session_id: オプションのセッション識別子

    Returns:
        ConversationMemory インスタンス
    """
    return ConversationMemory(user_id=user_id, session_id=session_id)
