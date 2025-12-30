"""Pytest configuration for integration tests"""
import os
import sys
import pytest
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env if it exists
try:
    from dotenv import load_dotenv
    env_file = project_root / 'tests' / '.env'
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    pass


@pytest.fixture(scope="session")
def aws_region():
    """Get AWS region from environment"""
    return os.environ.get('AWS_REGION', 'ap-northeast-1')


@pytest.fixture(scope="session")
def check_aws_credentials():
    """Verify AWS credentials are configured"""
    import boto3
    try:
        sts = boto3.client('sts')
        sts.get_caller_identity()
    except Exception as e:
        pytest.skip(f"AWS credentials not configured: {e}")
