import re
from slack_sdk import WebClient
from services.config import get_slack_bot_token

def get_slack_client():
   """Slack クライアントを取得"""
   token = get_slack_bot_token()
   return WebClient(token=token)

def post_message(channel: str, text: str, thread_ts: str = None, user_id: str = None):
   """Slack にメッセージを送信

   Args:
       channel: 送信先チャンネル
       text: メッセージ本文
       thread_ts: スレッドのタイムスタンプ (スレッド内返信の場合)
       user_id: メンション対象のユーザーID
   """
   client = get_slack_client()

   # ユーザーメンションを追加
   if user_id:
       text = f"<@{user_id}> {text}"

   # スレッド内返信または新規メッセージ
   result = client.chat_postMessage(
       channel=channel,
       text=text,
       thread_ts=thread_ts
   )
   return result
