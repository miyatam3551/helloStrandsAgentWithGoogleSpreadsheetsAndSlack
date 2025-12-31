import re
from slack_sdk import WebClient
from services.config import get_slack_bot_token

def get_slack_client():
   """Slack クライアントを取得"""
   token = get_slack_bot_token()
   return WebClient(token=token)

def post_message(channel: str, text: str, thread_ts: str = None):
   """Slack にメッセージを送信

   Args:
       channel: 送信先チャンネル ID
       text: メッセージテキスト
       thread_ts: スレッドのタイムスタンプ（スレッド内で返信する場合）

   Returns:
       Slack API のレスポンス
   """
   client = get_slack_client()

   result = client.chat_postMessage(
       channel=channel,
       text=text,
       thread_ts=thread_ts  # スレッド内に返信
   )
   return result
