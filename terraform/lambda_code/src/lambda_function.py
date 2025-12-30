import json
import os
import boto3
from strands import Agent
from tools.spreadsheet_tools import add_project
from tools.slack_tools import notify_slack
from services.slack_event_handler import handle_slack_event
from utils.slack_signature_verifier import verify_slack_signature

def get_signing_secret():
    """Parameter Store から Signing Secret を取得"""
    ssm = boto3.client('ssm', region_name=os.environ.get('AWS_REGION', 'ap-northeast-1'))
    param_name = os.environ.get('SLACK_SIGNING_SECRET_PARAM')

    if not param_name:
        raise ValueError("環境変数 SLACK_SIGNING_SECRET_PARAM が設定されていません")

    response = ssm.get_parameter(Name=param_name, WithDecryption=True)
    return response['Parameter']['Value']


def handler(event, context):
   """Lambda ハンドラー関数"""
   try:
       # イベントからボディを取得
       body_str = event.get('body', '{}')
       body = json.loads(body_str)

       # Slack Events API のチャレンジレスポンスを処理
       # チャレンジリクエストは署名検証の前に処理する必要がある
       if 'challenge' in body:
           return {
               'statusCode': 200,
               'body': json.dumps({'challenge': body['challenge']}),
               'headers': {'Content-Type': 'application/json'}
           }

       # Slack Events API からのイベントを処理
       if 'event' in body:
           # Slack からのリクエストの署名を検証
           headers = event.get('headers', {})
           timestamp = headers.get('X-Slack-Request-Timestamp') or headers.get('x-slack-request-timestamp')
           signature = headers.get('X-Slack-Signature') or headers.get('x-slack-signature')

           if not timestamp or not signature:
               return {
                   'statusCode': 401,
                   'body': json.dumps({'error': 'Missing Slack signature headers'}, ensure_ascii=False),
                   'headers': {'Content-Type': 'application/json'}
               }

           # Signing Secret を取得
           signing_secret = get_signing_secret()

           # 署名を検証
           try:
               is_valid = verify_slack_signature(signing_secret, timestamp, signature, body_str)
               if not is_valid:
                   return {
                       'statusCode': 401,
                       'body': json.dumps({'error': 'Invalid Slack signature'}, ensure_ascii=False),
                       'headers': {'Content-Type': 'application/json'}
                   }
           except ValueError as e:
               # タイムスタンプが古すぎる場合（リプレイ攻撃の可能性）
               return {
                   'statusCode': 401,
                   'body': json.dumps({'error': str(e)}, ensure_ascii=False),
                   'headers': {'Content-Type': 'application/json'}
               }

           # 署名が有効な場合、イベントを処理
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
