import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from services.config import get_google_credentials

def get_google_sheets_service():
   """Google Sheets サービスを取得"""
   # Parameter Store から認証情報取得
   credentials_json = get_google_credentials()
   credentials_dict = json.loads(credentials_json)

   credentials = service_account.Credentials.from_service_account_info(
       credentials_dict,
       scopes=['https://www.googleapis.com/auth/spreadsheets']
   )

   return build('sheets', 'v4', credentials=credentials)

def append_to_sheet(spreadsheet_id: str, range_name: str, values: list):
   """スプレッドシートにデータを追加"""
   service = get_google_sheets_service()
   body = {'values': values}

   result = service.spreadsheets().values().append(
       spreadsheetId=spreadsheet_id,
       range=range_name,
       valueInputOption='RAW',
       body=body
   ).execute()

   return result
