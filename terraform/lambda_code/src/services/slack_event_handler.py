"""Slack Events API のイベント処理"""
import os
from strands import Agent
from services.slack_service import post_message
from tools.spreadsheet_tools import add_project
from tools.slack_tools import notify_slack


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
    event_type = event_data.get('event', {}).get('type')

    if event_type == 'app_mention':
        return handle_app_mention(event_data)
    else:
        return {
            'success': False,
            'message': f'未対応のイベントタイプ: {event_type}'
        }
