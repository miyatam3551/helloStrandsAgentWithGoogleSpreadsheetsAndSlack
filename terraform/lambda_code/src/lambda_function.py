import json
import os
from strands import Agent
from tools.spreadsheet_tools import add_project
from tools.slack_tools import notify_slack
from services.slack_event_handler import handle_slack_event

def handler(event, context):
   """Lambda ハンドラー関数"""
   try:
       # デバッグ: イベント全体をログ出力
       print(f"[DEBUG] event: {json.dumps(event, ensure_ascii=False)}")

       # イベントからボディを取得
       body = json.loads(event.get('body', '{}'))
       print(f"[DEBUG] body: {json.dumps(body, ensure_ascii=False)}")
       print(f"[DEBUG] 'challenge' in body: {'challenge' in body}")

       # Slack Events API のチャレンジレスポンスを処理
       if 'challenge' in body:
           return {
               'statusCode': 200,
               'body': json.dumps({'challenge': body['challenge']}),
               'headers': {'Content-Type': 'application/json'}
           }

       # Slack Events API からのイベントを処理
       if 'event' in body:
           result = handle_slack_event(body)
           return {
               'statusCode': 200,
               'body': json.dumps(result, ensure_ascii=False),
               'headers': {'Content-Type': 'application/json'}
           }

       # 従来の直接呼び出し（HTTP POST /invoke）を処理
       prompt = body.get('prompt', 'テスト')

       # エージェントを初期化
       agent = Agent(
           system_prompt="あなたは親切なアシスタントです。Google Spreadsheet や Slack を操作できます。",
           tools=[add_project, notify_slack],
           model=os.environ.get('BEDROCK_MODEL_ID')
       )

       # プロンプトを処理
       response = agent(prompt)

       return {
           'statusCode': 200,
           'body': json.dumps({'message': str(response)}, ensure_ascii=False),
           'headers': {'Content-Type': 'application/json'}
       }
   except Exception as e:
       return {
           'statusCode': 500,
           'body': json.dumps({'error': str(e)}, ensure_ascii=False),
           'headers': {'Content-Type': 'application/json'}
       }
