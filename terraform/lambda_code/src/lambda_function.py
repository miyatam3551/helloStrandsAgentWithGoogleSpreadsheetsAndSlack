import json
import os
import boto3
from services.slack_event_handler import try_mark_event_as_processed, delete_event_record
from utils.slack_signature_verifier import verify_slack_signature

# Create clients at module level to reuse across Lambda invocations
ssm_client = boto3.client('ssm', region_name=os.environ.get('AWS_REGION', 'ap-northeast-1'))
sfn_client = boto3.client('stepfunctions', region_name=os.environ.get('AWS_REGION', 'ap-northeast-1'))

def get_signing_secret():
    """Parameter Store から Signing Secret を取得"""
    param_name = os.environ.get('SLACK_SIGNING_SECRET_PARAM')

    if not param_name:
        raise ValueError("環境変数 SLACK_SIGNING_SECRET_PARAM が設定されていません")

    response = ssm_client.get_parameter(Name=param_name, WithDecryption=True)
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

           # 署名が有効な場合、Step Functionsで非同期処理を開始
           # 重複チェック済みなので、Step Functionsを起動
           state_machine_arn = os.environ.get('STATE_MACHINE_ARN')
           if not state_machine_arn:
               raise ValueError("環境変数 STATE_MACHINE_ARN が設定されていません")

           # Step Functions実行を開始（非同期）
           try:
               execution_response = sfn_client.start_execution(
                   stateMachineArn=state_machine_arn,
                   input=json.dumps(body)
               )
               print(f"Step Functions実行開始: {execution_response['executionArn']}")
           except Exception as sfn_error:
               # Step Functions起動失敗時は、DynamoDBレコードを削除（ロールバック）
               print(f"Step Functions起動失敗: {sfn_error}")
               if event_id:
                   delete_event_record(event_id)
               # エラーを再送出して、呼び出し元に通知
               raise

           # 即座に200 OKを返す（Slackがタイムアウトしない）
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
