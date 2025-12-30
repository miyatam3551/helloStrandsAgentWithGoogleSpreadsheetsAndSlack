"""
AI処理専用Lambda関数
Step Functionsから呼び出されて、Slackイベントを処理する
"""
import json
from services.slack_event_handler import handle_slack_event


def handler(event, context):
    """
    Step Functionsから呼び出されるハンドラー

    Args:
        event: Step Functionsから渡されるSlackイベントデータ
        context: Lambda実行コンテキスト

    Returns:
        処理結果
    """
    try:
        # Slackイベントを処理
        result = handle_slack_event(event)

        return {
            'statusCode': 200,
            'body': json.dumps(result, ensure_ascii=False)
        }
    except Exception as e:
        print(f"処理エラー: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}, ensure_ascii=False)
        }
