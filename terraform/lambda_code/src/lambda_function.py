import json
import os
from strands import Agent
from tools.spreadsheet_tools import add_project
from tools.slack_tools import notify_slack

def handler(event, context):
   """Lambda ハンドラー関数"""
   try:
       # イベントからプロンプトを取得
       body = json.loads(event.get('body', '{}'))
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
           'body': json.dumps({'message': str(response)}, ensure_ascii=False)
       }
   except Exception as e:
       return {
           'statusCode': 500,
           'body': json.dumps({'error': str(e)}, ensure_ascii=False)
       }
