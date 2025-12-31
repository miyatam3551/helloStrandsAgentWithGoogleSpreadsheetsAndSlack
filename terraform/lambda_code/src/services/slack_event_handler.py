"""Slack Events API のイベント処理"""
import os
import time
import boto3
from strands import Agent
from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager
from services.slack_service import post_message
from tools.spreadsheet_tools import add_project
from tools.slack_tools import notify_slack

# DynamoDB クライアントの初期化
dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'ap-northeast-1'))
table_name = os.environ.get('DYNAMODB_TABLE_NAME')


def try_mark_event_as_processed(event_id: str, ttl_hours: int = 24) -> bool:
    """イベントを処理済みとしてマーク（アトミック操作）

    条件付き書き込みを使用して、イベントIDがまだ存在しない場合のみ書き込む。
    これにより、複数のLambda呼び出しが同時に実行されても、
    最初の1つだけが成功し、他は重複として扱われる。

    Args:
        event_id: Slack イベント ID
        ttl_hours: イベント記録の有効期限（時間単位）。デフォルトは 24 時間

    Returns:
        書き込みに成功した場合（初めてのイベント）は True、
        すでに存在する場合（重複イベント）は False
    """
    if not table_name or not event_id:
        # テーブル名やイベントIDがない場合は、安全のため処理を許可
        return True

    try:
        table = dynamodb.Table(table_name)
        expiration_time = int(time.time()) + (ttl_hours * 3600)

        # 条件付き書き込み: event_id が存在しない場合のみ書き込む
        table.put_item(
            Item={
                'event_id': event_id,
                'processed_at': int(time.time()),
                'expiration_time': expiration_time
            },
            ConditionExpression='attribute_not_exists(event_id)'
        )
        # 書き込み成功 = 初めてのイベント
        return True

    except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
        # 条件チェック失敗 = すでに存在する = 重複イベント
        print(f"重複イベントを検出しました: {event_id}")
        return False

    except Exception as e:
        print(f"DynamoDB エラー (put_item): {e}")
        # その他のエラーの場合は、安全のため処理を許可
        return True


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
    thread_ts = event.get('thread_ts') or event.get('ts')  # スレッドまたは元メッセージのタイムスタンプ

    # ボットのメンション部分を削除（例: <@U12345678> こんにちは → こんにちは）
    import re
    clean_text = re.sub(r'<@[A-Z0-9]+>', '', text).strip()

    if not clean_text:
        clean_text = "こんにちは！何かお手伝いできることはありますか？"

    # AgentCore Memory の設定
    memory_config = AgentCoreMemoryConfig(
        user_id=user,
        session_id=thread_ts  # スレッドをセッションとして使用
    )

    # セッションマネージャーを使用してエージェントを初期化
    session_manager = AgentCoreMemorySessionManager(config=memory_config)

    # エージェントを初期化（セッションマネージャー経由）
    agent = session_manager.create_agent(
        system_prompt="""あなたはシティーハンターの海坊主の口調で話すエージェント。
以下の制約を厳守せよ。

・基本は短文。1文は最大20文字程度。
・一人称は「俺」。
・感嘆符や絵文字は使わない。
・軽口、冗談、説明過多は禁止。
・結論を先に述べる。
・感情は言葉にせず、行動や判断で示す。
・語尾は「〜だ」「〜だな」「問題ない」「やるか」「覚悟はいいか」などを多用。
・相手を励ますときも、長い共感はしない。
  例:「怖いか? だが進むぞ。」

話し方の雰囲気:
低音、寡黙、威圧感があるが無駄に荒くない。

あなたは Google Spreadsheet や Slack を操作できる。
ユーザーとの過去の会話を覚えていて、ユーザーの好みや傾向を理解している。""",
        tools=[add_project, notify_slack],
        model=os.environ.get('BEDROCK_MODEL_ID')
    )

    # プロンプトを処理
    response = agent(clean_text)

    # 応答を同じスレッド内でユーザーにメンションして送信
    try:
        post_message(channel, str(response), thread_ts=thread_ts, user_id=user)
    except Exception as e:
        # Slack へのメッセージ送信に失敗しても、Lambda は成功として返す
        # これにより、Slack の無限再送を防ぐ
        print(f"Slack へのメッセージ送信に失敗しました: {e}")
        return {
            'success': False,
            'message': f'Slack へのメッセージ送信に失敗: {str(e)}',
            'channel': channel,
            'response': str(response)
        }

    return {
        'success': True,
        'message': 'メンションに応答しました',
        'channel': channel,
        'user': user,
        'thread_ts': thread_ts,
        'response': str(response)
    }


def handle_slack_event(event_data: dict) -> dict:
    """Slack イベントを処理

    Args:
        event_data: Slack Events API から受け取ったイベントデータ

    Returns:
        処理結果を含む辞書

    Note:
        重複チェックは lambda_function.py で既に実行済み
    """
    event_type = event_data.get('event', {}).get('type')

    if event_type == 'app_mention':
        return handle_app_mention(event_data)
    else:
        return {
            'success': False,
            'message': f'未対応のイベントタイプ: {event_type}'
        }
