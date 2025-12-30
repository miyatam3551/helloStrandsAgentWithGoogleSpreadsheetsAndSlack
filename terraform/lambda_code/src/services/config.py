"""Parameter Store から設定値を取得する共通モジュール"""
import boto3

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
   return get_parameter('/bp-management/spreadsheet-id', with_decryption=True)

def get_google_credentials() -> str:
   """Google サービスアカウント認証情報を取得"""
   return get_parameter('/bp-management/google-credentials', with_decryption=True)

def get_slack_bot_token() -> str:
   """Slack Bot Token を取得"""
   return get_parameter('/bp-management/slack-bot-token', with_decryption=True)
