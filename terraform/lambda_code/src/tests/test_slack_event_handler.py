"""Slack イベントハンドラのユニットテスト"""
import os
import time
from unittest.mock import Mock, patch, MagicMock
import pytest
from botocore.exceptions import ClientError


class TestTryMarkEventAsProcessed:
    """try_mark_event_as_processed 関数のテストクラス"""

    @patch.dict(os.environ, {'DYNAMODB_TABLE_NAME': 'test-table', 'AWS_REGION': 'ap-northeast-1'})
    @patch('services.slack_event_handler.dynamodb')
    def test_first_event_returns_true(self, mock_dynamodb):
        """初めてのイベントで True を返すことを確認"""
        from services.slack_event_handler import try_mark_event_as_processed

        # DynamoDB の Table モックを作成
        mock_table = Mock()
        mock_dynamodb.Table.return_value = mock_table
        # put_item が成功する（例外が発生しない）
        mock_table.put_item.return_value = {}

        event_id = "test_event_123"
        result = try_mark_event_as_processed(event_id)

        assert result is True
        # put_item が呼ばれたことを確認
        mock_table.put_item.assert_called_once()
        # 条件式が正しいことを確認
        call_args = mock_table.put_item.call_args
        assert call_args[1]['ConditionExpression'] == 'attribute_not_exists(event_id)'
        assert call_args[1]['Item']['event_id'] == event_id

    @patch.dict(os.environ, {'DYNAMODB_TABLE_NAME': 'test-table', 'AWS_REGION': 'ap-northeast-1'})
    @patch('services.slack_event_handler.dynamodb')
    def test_duplicate_event_returns_false(self, mock_dynamodb):
        """重複イベントで False を返すことを確認"""
        from services.slack_event_handler import try_mark_event_as_processed

        # DynamoDB の Table モックを作成
        mock_table = Mock()
        mock_dynamodb.Table.return_value = mock_table

        # ConditionalCheckFailedException をスローするように設定
        mock_client = Mock()
        mock_client.exceptions.ConditionalCheckFailedException = type(
            'ConditionalCheckFailedException',
            (Exception,),
            {}
        )
        mock_dynamodb.meta.client = mock_client

        exception = mock_client.exceptions.ConditionalCheckFailedException()
        mock_table.put_item.side_effect = exception

        event_id = "duplicate_event_456"
        result = try_mark_event_as_processed(event_id)

        assert result is False
        mock_table.put_item.assert_called_once()

    @patch.dict(os.environ, {'DYNAMODB_TABLE_NAME': 'test-table', 'AWS_REGION': 'ap-northeast-1'})
    @patch('services.slack_event_handler.dynamodb')
    def test_other_error_returns_true(self, mock_dynamodb):
        """その他のエラーで True を返すことを確認（安全のため処理を許可）"""
        from services.slack_event_handler import try_mark_event_as_processed

        # DynamoDB の Table モックを作成
        mock_table = Mock()
        mock_dynamodb.Table.return_value = mock_table

        # 一般的なエラーをスローするように設定
        mock_table.put_item.side_effect = Exception("Network error")

        event_id = "error_event_789"
        result = try_mark_event_as_processed(event_id)

        assert result is True
        mock_table.put_item.assert_called_once()

    @patch.dict(os.environ, {'DYNAMODB_TABLE_NAME': '', 'AWS_REGION': 'ap-northeast-1'})
    def test_no_table_name_returns_true(self):
        """テーブル名がない場合に True を返すことを確認"""
        from services.slack_event_handler import try_mark_event_as_processed

        event_id = "test_event_no_table"
        result = try_mark_event_as_processed(event_id)

        assert result is True

    @patch.dict(os.environ, {'DYNAMODB_TABLE_NAME': 'test-table', 'AWS_REGION': 'ap-northeast-1'})
    def test_no_event_id_returns_true(self):
        """イベント ID がない場合に True を返すことを確認"""
        from services.slack_event_handler import try_mark_event_as_processed

        result = try_mark_event_as_processed("")

        assert result is True

    @patch.dict(os.environ, {'DYNAMODB_TABLE_NAME': 'test-table', 'AWS_REGION': 'ap-northeast-1'})
    @patch('services.slack_event_handler.dynamodb')
    @patch('services.slack_event_handler.time.time')
    def test_ttl_calculation_default(self, mock_time, mock_dynamodb):
        """デフォルトの TTL（24時間）が正しく計算されることを確認"""
        from services.slack_event_handler import try_mark_event_as_processed

        # 現在時刻を固定
        current_time = 1000000
        mock_time.return_value = current_time

        mock_table = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.put_item.return_value = {}

        event_id = "ttl_test_event"
        try_mark_event_as_processed(event_id)

        # put_item の呼び出し引数を確認
        call_args = mock_table.put_item.call_args
        item = call_args[1]['Item']

        # デフォルトの TTL は 24 時間
        expected_expiration = current_time + (24 * 3600)
        assert item['expiration_time'] == expected_expiration
        assert item['processed_at'] == current_time

    @patch.dict(os.environ, {'DYNAMODB_TABLE_NAME': 'test-table', 'AWS_REGION': 'ap-northeast-1'})
    @patch('services.slack_event_handler.dynamodb')
    @patch('services.slack_event_handler.time.time')
    def test_ttl_calculation_custom(self, mock_time, mock_dynamodb):
        """カスタム TTL が正しく計算されることを確認"""
        from services.slack_event_handler import try_mark_event_as_processed

        # 現在時刻を固定
        current_time = 1000000
        mock_time.return_value = current_time

        mock_table = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.put_item.return_value = {}

        event_id = "ttl_custom_event"
        custom_ttl_hours = 48
        try_mark_event_as_processed(event_id, ttl_hours=custom_ttl_hours)

        # put_item の呼び出し引数を確認
        call_args = mock_table.put_item.call_args
        item = call_args[1]['Item']

        # カスタム TTL は 48 時間
        expected_expiration = current_time + (48 * 3600)
        assert item['expiration_time'] == expected_expiration

    @patch.dict(os.environ, {'DYNAMODB_TABLE_NAME': 'test-table', 'AWS_REGION': 'ap-northeast-1'})
    @patch('services.slack_event_handler.dynamodb')
    def test_conditional_expression_prevents_overwrite(self, mock_dynamodb):
        """条件式により既存のイベント ID が上書きされないことを確認"""
        from services.slack_event_handler import try_mark_event_as_processed

        mock_table = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.put_item.return_value = {}

        event_id = "conditional_test_event"
        try_mark_event_as_processed(event_id)

        # 条件式が attribute_not_exists であることを確認
        call_args = mock_table.put_item.call_args
        condition_expr = call_args[1]['ConditionExpression']
        assert condition_expr == 'attribute_not_exists(event_id)'

    @patch.dict(os.environ, {'DYNAMODB_TABLE_NAME': 'test-table', 'AWS_REGION': 'ap-northeast-1'})
    @patch('services.slack_event_handler.dynamodb')
    def test_multiple_events_same_id(self, mock_dynamodb):
        """同じイベント ID で複数回呼ばれた場合の動作を確認"""
        from services.slack_event_handler import try_mark_event_as_processed

        mock_table = Mock()
        mock_dynamodb.Table.return_value = mock_table

        # ConditionalCheckFailedException の設定
        mock_client = Mock()
        mock_client.exceptions.ConditionalCheckFailedException = type(
            'ConditionalCheckFailedException',
            (Exception,),
            {}
        )
        mock_dynamodb.meta.client = mock_client

        # 1回目は成功、2回目は失敗するように設定
        exception = mock_client.exceptions.ConditionalCheckFailedException()
        mock_table.put_item.side_effect = [
            {},  # 1回目は成功
            exception  # 2回目は ConditionalCheckFailedException
        ]

        event_id = "same_event_id"

        # 1回目
        result1 = try_mark_event_as_processed(event_id)
        assert result1 is True

        # 2回目（重複）
        result2 = try_mark_event_as_processed(event_id)
        assert result2 is False

        # put_item が2回呼ばれたことを確認
        assert mock_table.put_item.call_count == 2
