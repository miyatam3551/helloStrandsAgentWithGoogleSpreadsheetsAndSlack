"""Pytest configuration for integration tests"""
import os
import sys
import time
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


@pytest.fixture(scope="class")
def aws_resources(aws_region):
    """Setup AWS resources for integration testing
    
    This fixture provides AWS clients and resource information
    needed for integration tests.
    """
    import boto3
    
    # Initialize AWS clients
    dynamodb = boto3.resource('dynamodb', region_name=aws_region)
    sfn_client = boto3.client('stepfunctions', region_name=aws_region)
    lambda_client = boto3.client('lambda', region_name=aws_region)
    
    # Get resource names from environment or Terraform outputs
    table_name = os.environ.get('DYNAMODB_TABLE_NAME')
    state_machine_arn = os.environ.get('STATE_MACHINE_ARN')
    lambda_function_name = os.environ.get('LAMBDA_FUNCTION_NAME')
    
    if not table_name or not state_machine_arn or not lambda_function_name:
        pytest.skip(
            "AWS resources not configured. Please set environment variables:\n"
            "  DYNAMODB_TABLE_NAME, STATE_MACHINE_ARN, LAMBDA_FUNCTION_NAME\n"
            "Run './setup_test_env.sh' to automatically configure from Terraform outputs."
        )
    
    return {
        'dynamodb': dynamodb,
        'sfn_client': sfn_client,
        'lambda_client': lambda_client,
        'table_name': table_name,
        'state_machine_arn': state_machine_arn,
        'lambda_function_name': lambda_function_name,
        'table': dynamodb.Table(table_name)
    }


def count_recent_executions(sfn_client, state_machine_arn: str, seconds: int = 60) -> int:
    """Count Step Functions executions in the last N seconds
    
    Helper function to check how many executions were started recently.
    
    Args:
        sfn_client: Boto3 Step Functions client
        state_machine_arn: ARN of the state machine
        seconds: Time window to check (default 60 seconds)
        
    Returns:
        Number of executions
    """
    try:
        response = sfn_client.list_executions(
            stateMachineArn=state_machine_arn,
            maxResults=100
        )
        
        current_time = time.time()
        recent_executions = [
            e for e in response['executions']
            if (current_time - e['startDate'].timestamp()) < seconds
        ]
        
        return len(recent_executions)
    except Exception as e:
        print(f"Warning: Could not count executions: {e}")
        return 0
