import re
from slack_sdk import WebClient
from services.config import get_slack_bot_token

def get_slack_client():
   """Slack クライアントを取得"""
   token = get_slack_bot_token()
   return WebClient(token=token)

def post_message(channel: str, text: str):
   """Slack にメッセージを送信"""
   client = get_slack_client()

   result = client.chat_postMessage(
       channel=channel,
       text=text
   )
   return result
