"""Parameter Store から設定値を取得する共通モジュール"""
import boto3
import os

ssm = boto3.client('ssm', region_name='ap-northeast-1')

def get_parameter(name: str, with_decryption: bool = False) -> str:
   """Parameter Store からパラメータを取得

   Args:
       name: パラメータ名
       with_decryption: 復号化するかどうか

   Returns:
       パラメータの値
   """
   response = ssm.get_parameter(
       Name=name,
       WithDecryption=with_decryption
   )
   return response['Parameter']['Value']

def get_spreadsheet_id() -> str:
   """Spreadsheet ID を取得"""
   param_name = os.environ['PARAM_SPREADSHEET_ID']
   return get_parameter(param_name, with_decryption=True)

def get_google_credentials() -> str:
   """Google サービスアカウント認証情報を取得"""
   param_name = os.environ['PARAM_GOOGLE_CREDENTIALS']
   return get_parameter(param_name, with_decryption=True)

def get_slack_bot_token() -> str:
   """Slack Bot Token を取得"""
   param_name = os.environ['PARAM_SLACK_BOT_TOKEN']
   return get_parameter(param_name, with_decryption=True)
