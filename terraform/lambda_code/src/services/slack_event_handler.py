"""Slack Events API のイベント処理"""
import os
import time
import boto3
from strands import Agent
from services.slack_service import post_message
from tools.spreadsheet_tools import add_project
from tools.slack_tools import notify_slack

# DynamoDB クライアントの初期化
dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('BEDROCK_REGION', 'us-east-1'))
table_name = os.environ.get('DYNAMODB_TABLE_NAME')


def is_duplicate_event(event_id: str) -> bool:
    """イベントが重複しているかチェック

    Args:
        event_id: Slack イベント ID

    Returns:
        重複している場合は True、初めてのイベントの場合は False
    """
    if not table_name or not event_id:
        return False

    try:
        table = dynamodb.Table(table_name)
        response = table.get_item(Key={'event_id': event_id})
        return 'Item' in response
    except Exception as e:
        print(f"DynamoDB エラー (get_item): {e}")
        # エラーが発生した場合は、安全のため重複として扱わない（処理を続行）
        return False


def mark_event_as_processed(event_id: str, ttl_hours: int = 24) -> None:
    """イベントを処理済みとしてマーク

    Args:
        event_id: Slack イベント ID
        ttl_hours: イベント記録の有効期限（時間単位）。デフォルトは 24 時間
    """
    if not table_name or not event_id:
        return

    try:
        table = dynamodb.Table(table_name)
        expiration_time = int(time.time()) + (ttl_hours * 3600)
        table.put_item(
            Item={
                'event_id': event_id,
                'processed_at': int(time.time()),
                'expiration_time': expiration_time
            }
        )
    except Exception as e:
        print(f"DynamoDB エラー (put_item): {e}")


def handle_app_mention(event_data: dict) -> dict:
    """app_mention イベントを処理

    Args:
        event_data: Slack Events API から受け取ったイベントデータ

    Returns:
        処理結果を含む辞書
    """
    event = event_data.get('event', {})

    # メンションされたメッセージのテキストを取得
    text = event.get('text', '')
    channel = event.get('channel', '')
    user = event.get('user', '')

    # ボットのメンション部分を削除（例: <@U12345678> こんにちは → こんにちは）
    # bot_user_id = event.get('bot_id')
    import re
    clean_text = re.sub(r'<@[A-Z0-9]+>', '', text).strip()

    if not clean_text:
        clean_text = "こんにちは！何かお手伝いできることはありますか？"

    # エージェントを初期化
    agent = Agent(
        system_prompt="あなたは親切なアシスタントです。Google Spreadsheet や Slack を操作できます。",
        tools=[add_project, notify_slack],
        model=os.environ.get('BEDROCK_MODEL_ID')
    )

    # プロンプトを処理
    response = agent(clean_text)

    # 応答を同じチャンネルに送信
    post_message(channel, str(response))

    return {
        'success': True,
        'message': 'メンションに応答しました',
        'channel': channel,
        'response': str(response)
    }


def handle_slack_event(event_data: dict) -> dict:
    """Slack イベントを処理

    Args:
        event_data: Slack Events API から受け取ったイベントデータ

    Returns:
        処理結果を含む辞書
    """
    # イベント ID を取得して重複チェック
    event_id = event_data.get('event_id')

    if event_id:
        if is_duplicate_event(event_id):
            print(f"重複イベントを検出しました: {event_id}")
            return {
                'success': True,
                'message': '重複イベントのためスキップしました',
                'event_id': event_id
            }

        # イベントを処理済みとしてマーク
        mark_event_as_processed(event_id)

    event_type = event_data.get('event', {}).get('type')

    if event_type == 'app_mention':
        return handle_app_mention(event_data)
    else:
        return {
            'success': False,
            'message': f'未対応のイベントタイプ: {event_type}'
        }
