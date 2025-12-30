"""Test utilities for integration tests"""
import hashlib
import hmac
import json
import time
from typing import Dict, Any


def generate_slack_signature(signing_secret: str, timestamp: str, body: str) -> str:
    """Generate a valid Slack signature for testing
    
    Args:
        signing_secret: Slack App Signing Secret
        timestamp: Request timestamp
        body: Request body as string
        
    Returns:
        Signature string in format 'v0=...'
    """
    sig_basestring = f"v0:{timestamp}:{body}"
    signature = 'v0=' + hmac.new(
        signing_secret.encode('utf-8'),
        sig_basestring.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature


def create_slack_event_payload(
    event_type: str = "app_mention",
    event_id: str = None,
    text: str = "Hello",
    channel: str = "C12345678",
    user: str = "U12345678"
) -> Dict[str, Any]:
    """Create a Slack Events API payload for testing
    
    Args:
        event_type: Type of event (e.g., 'app_mention')
        event_id: Unique event ID (auto-generated if not provided)
        text: Message text
        channel: Channel ID
        user: User ID
        
    Returns:
        Dictionary representing Slack Events API payload
    """
    if event_id is None:
        event_id = f"Ev{int(time.time() * 1000000)}"
    
    return {
        "token": "test_verification_token",
        "team_id": "T12345678",
        "api_app_id": "A12345678",
        "event": {
            "type": event_type,
            "text": text,
            "channel": channel,
            "user": user,
            "ts": str(time.time())
        },
        "type": "event_callback",
        "event_id": event_id,
        "event_time": int(time.time())
    }


def create_api_gateway_event(
    body: Dict[str, Any],
    signing_secret: str,
    timestamp: str = None
) -> Dict[str, Any]:
    """Create an API Gateway event for Lambda testing
    
    Args:
        body: Request body (will be JSON encoded)
        signing_secret: Slack Signing Secret for signature generation
        timestamp: Request timestamp (auto-generated if not provided)
        
    Returns:
        Dictionary representing API Gateway event
    """
    if timestamp is None:
        timestamp = str(int(time.time()))
    
    body_str = json.dumps(body)
    signature = generate_slack_signature(signing_secret, timestamp, body_str)
    
    return {
        "body": body_str,
        "headers": {
            "X-Slack-Request-Timestamp": timestamp,
            "X-Slack-Signature": signature,
            "Content-Type": "application/json"
        },
        "requestContext": {
            "http": {
                "method": "POST",
                "path": "/slack/events"
            }
        }
    }
