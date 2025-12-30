"""Slack 署名検証ロジックのユニットテスト"""
import hashlib
import hmac
import time
import pytest
from utils.slack_signature_verifier import verify_slack_signature


class TestVerifySlackSignature:
    """verify_slack_signature 関数のテストクラス"""

    def test_valid_signature(self):
        """正しい署名で検証が成功することを確認"""
        signing_secret = "test_secret_12345"
        timestamp = str(int(time.time()))
        body = '{"type":"event_callback","event":{"type":"app_mention"}}'

        # 正しい署名を生成
        sig_basestring = f"v0:{timestamp}:{body}"
        expected_signature = 'v0=' + hmac.new(
            signing_secret.encode('utf-8'),
            sig_basestring.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        result = verify_slack_signature(signing_secret, timestamp, expected_signature, body)
        assert result is True

    def test_invalid_signature(self):
        """誤った署名で検証が失敗することを確認"""
        signing_secret = "test_secret_12345"
        timestamp = str(int(time.time()))
        body = '{"type":"event_callback"}'
        invalid_signature = "v0=invalid_signature_hash"

        result = verify_slack_signature(signing_secret, timestamp, invalid_signature, body)
        assert result is False

    def test_wrong_signing_secret(self):
        """異なる Signing Secret で検証が失敗することを確認"""
        signing_secret = "test_secret_12345"
        wrong_secret = "wrong_secret_67890"
        timestamp = str(int(time.time()))
        body = '{"type":"event_callback"}'

        # 間違ったシークレットで署名を生成
        sig_basestring = f"v0:{timestamp}:{body}"
        signature = 'v0=' + hmac.new(
            wrong_secret.encode('utf-8'),
            sig_basestring.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        result = verify_slack_signature(signing_secret, timestamp, signature, body)
        assert result is False

    def test_tampered_body(self):
        """リクエストボディが改ざんされた場合に検証が失敗することを確認"""
        signing_secret = "test_secret_12345"
        timestamp = str(int(time.time()))
        original_body = '{"type":"event_callback","event":{"type":"app_mention"}}'
        tampered_body = '{"type":"event_callback","event":{"type":"message"}}'

        # オリジナルのボディで署名を生成
        sig_basestring = f"v0:{timestamp}:{original_body}"
        signature = 'v0=' + hmac.new(
            signing_secret.encode('utf-8'),
            sig_basestring.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        # 改ざんされたボディで検証
        result = verify_slack_signature(signing_secret, timestamp, signature, tampered_body)
        assert result is False

    def test_replay_attack_old_timestamp(self):
        """古すぎるタイムスタンプでリプレイ攻撃を防ぐことを確認"""
        signing_secret = "test_secret_12345"
        # 6分前のタイムスタンプ（5分を超えている）
        old_timestamp = str(int(time.time()) - 360)
        body = '{"type":"event_callback"}'

        sig_basestring = f"v0:{old_timestamp}:{body}"
        signature = 'v0=' + hmac.new(
            signing_secret.encode('utf-8'),
            sig_basestring.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        with pytest.raises(ValueError, match="リクエストのタイムスタンプが古すぎます"):
            verify_slack_signature(signing_secret, old_timestamp, signature, body)

    def test_replay_attack_future_timestamp(self):
        """未来のタイムスタンプでリプレイ攻撃を防ぐことを確認"""
        signing_secret = "test_secret_12345"
        # 6分後のタイムスタンプ（5分を超えている）
        future_timestamp = str(int(time.time()) + 360)
        body = '{"type":"event_callback"}'

        sig_basestring = f"v0:{future_timestamp}:{body}"
        signature = 'v0=' + hmac.new(
            signing_secret.encode('utf-8'),
            sig_basestring.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        with pytest.raises(ValueError, match="リクエストのタイムスタンプが古すぎます"):
            verify_slack_signature(signing_secret, future_timestamp, signature, body)

    def test_timestamp_within_tolerance(self):
        """許容範囲内のタイムスタンプで検証が成功することを確認"""
        signing_secret = "test_secret_12345"
        # 4分前のタイムスタンプ（5分以内）
        timestamp = str(int(time.time()) - 240)
        body = '{"type":"event_callback"}'

        sig_basestring = f"v0:{timestamp}:{body}"
        signature = 'v0=' + hmac.new(
            signing_secret.encode('utf-8'),
            sig_basestring.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        result = verify_slack_signature(signing_secret, timestamp, signature, body)
        assert result is True

    def test_empty_body(self):
        """空のリクエストボディでも検証が正しく動作することを確認"""
        signing_secret = "test_secret_12345"
        timestamp = str(int(time.time()))
        body = ""

        sig_basestring = f"v0:{timestamp}:{body}"
        signature = 'v0=' + hmac.new(
            signing_secret.encode('utf-8'),
            sig_basestring.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        result = verify_slack_signature(signing_secret, timestamp, signature, body)
        assert result is True

    def test_special_characters_in_body(self):
        """特殊文字を含むボディで検証が正しく動作することを確認"""
        signing_secret = "test_secret_12345"
        timestamp = str(int(time.time()))
        body = '{"text":"こんにちは！😀 テスト & <@U12345> #channel"}'

        sig_basestring = f"v0:{timestamp}:{body}"
        signature = 'v0=' + hmac.new(
            signing_secret.encode('utf-8'),
            sig_basestring.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        result = verify_slack_signature(signing_secret, timestamp, signature, body)
        assert result is True
