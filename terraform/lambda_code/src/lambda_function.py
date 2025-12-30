import json
import os
import boto3
import threading
from strands import Agent
from tools.spreadsheet_tools import add_project
from tools.slack_tools import notify_slack
from services.slack_event_handler import handle_slack_event, try_mark_event_as_processed
from utils.slack_signature_verifier import verify_slack_signature

# Create SSM client at module level to reuse across Lambda invocations
ssm_client = boto3.client('ssm', region_name=os.environ.get('AWS_REGION', 'ap-northeast-1'))

def get_signing_secret():
    """Parameter Store から Signing Secret を取得"""
    param_name = os.environ.get('SLACK_SIGNING_SECRET_PARAM')

    if not param_name:
        raise ValueError("環境変数 SLACK_SIGNING_SECRET_PARAM が設定されていません")

    response = ssm_client.get_parameter(Name=param_name, WithDecryption=True)
    return response['Parameter']['Value']


def process_event_async(body):
    """バックグラウンドでイベントを処理"""
    try:
        handle_slack_event(body)
    except Exception as e:
        print(f"バックグラウンド処理エラー: {e}")


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

           # 重複チェックを先に行う（アトミック操作）
           event_id = body.get('event_id')
           if event_id:
               if not try_mark_event_as_processed(event_id):
                   # 重複イベント - 即座に200 OKを返す
                   print(f"重複イベントをスキップ: {event_id}")
                   return {
                       'statusCode': 200,
                       'body': json.dumps({'ok': True, 'message': 'duplicate event'}),
                       'headers': {'Content-Type': 'application/json'}
                   }

           # 署名が有効な場合、バックグラウンドでイベントを処理
           # Slackは3秒以内に200 OKを受け取らないとタイムアウトでリトライするため、
           # 即座にレスポンスを返してから、バックグラウンドで処理を続ける
           thread = threading.Thread(target=process_event_async, args=(body,))
           thread.start()

           return {
               'statusCode': 200,
               'body': json.dumps({'ok': True}),
               'headers': {'Content-Type': 'application/json'}
           }

       # 認証されていないリクエストを拒否
       # Slack Events API 以外のリクエストは受け付けない
       return {
           'statusCode': 403,
           'body': json.dumps({
               'error': 'Forbidden',
               'message': 'このエンドポイントは Slack Events API からのリクエストのみ受け付けます。'
           }, ensure_ascii=False),
           'headers': {'Content-Type': 'application/json'}
       }
   except Exception as e:
       return {
           'statusCode': 500,
           'body': json.dumps({'error': str(e)}, ensure_ascii=False),
           'headers': {'Content-Type': 'application/json'}
       }
