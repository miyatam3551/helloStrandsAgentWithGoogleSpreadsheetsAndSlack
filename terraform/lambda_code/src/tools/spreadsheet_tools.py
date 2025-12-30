from datetime import datetime
from strands import tool
from services.google_sheets import append_to_sheet
from services.config import get_spreadsheet_id

@tool
def add_project(project_id: str, employee_name: str, tech_stack: str) -> dict:
   """案件をスプレッドシートに追加する

   Args:
       project_id: 案件ID
       employee_name: 担当者名
       tech_stack: 技術スタック

   Returns:
       成功メッセージを含む辞書
   """
   spreadsheet_id = get_spreadsheet_id()
   values = [[
       project_id,
       employee_name,
       '',  # employee_slack_id
       tech_stack,
       '', '', '', '', '', '募集中', '', datetime.now().isoformat()
   ]]

   append_to_sheet(spreadsheet_id, '案件!A2', values)
   return {'success': True, 'message': '案件を追加しました'}
