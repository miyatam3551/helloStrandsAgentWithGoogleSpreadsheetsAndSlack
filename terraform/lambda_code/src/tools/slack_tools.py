from strands import tool
from services.slack_service import post_message

@tool
def notify_slack(channel: str, message: str) -> dict:
   """Slack にメッセージを送信する

   Args:
       channel: チャンネル名（例: #general）
       message: 送信するメッセージ

   Returns:
       成功メッセージを含む辞書
   """
   post_message(channel, message)
   return {'success': True, 'message': 'Slack に通知しました'}
