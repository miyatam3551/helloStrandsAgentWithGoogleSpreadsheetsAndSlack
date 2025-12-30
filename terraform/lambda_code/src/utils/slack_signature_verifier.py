"""Slack Signing Secret による署名検証"""
import hashlib
import hmac
import time


def verify_slack_signature(
    signing_secret: str,
    timestamp: str,
    signature: str,
    body: str
) -> bool:
    """Slack リクエストの署名を検証

    Slack Events API からのリクエストが正当なものであることを検証する。
    署名検証により、悪意のあるユーザーが偽のリクエストを送信することを防ぐ。

    Args:
        signing_secret: Slack App の Signing Secret
        timestamp: リクエストヘッダーの X-Slack-Request-Timestamp
        signature: リクエストヘッダーの X-Slack-Signature
        body: リクエストボディ（生の文字列）

    Returns:
        署名が有効な場合は True、無効な場合は False

    Raises:
        ValueError: タイムスタンプが古すぎる場合（リプレイ攻撃の可能性）
    """
    # タイムスタンプのリプレイ攻撃チェック（5分以上古いリクエストは拒否）
    current_timestamp = int(time.time())
    request_timestamp = int(timestamp)

    if abs(current_timestamp - request_timestamp) > 60 * 5:
        raise ValueError(
            f"リクエストのタイムスタンプが古すぎます。"
            f"現在時刻: {current_timestamp}, リクエスト時刻: {request_timestamp}"
        )

    # 署名のベース文字列を作成
    sig_basestring = f"v0:{timestamp}:{body}"

    # HMAC-SHA256 で署名を計算
    computed_signature = 'v0=' + hmac.new(
        signing_secret.encode('utf-8'),
        sig_basestring.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    # 署名を比較（タイミング攻撃を防ぐため hmac.compare_digest を使用）
    return hmac.compare_digest(computed_signature, signature)
