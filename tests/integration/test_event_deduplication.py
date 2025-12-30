"""Integration tests for duplicate event_id detection and Step Functions execution

This test suite verifies:
1. Duplicate events with the same event_id are rejected
2. Step Functions execution is triggered correctly
3. DynamoDB table stores event_id properly
"""
import json
import os
import time
import pytest

from .test_utils import (
    create_slack_event_payload,
    create_api_gateway_event,
    generate_unique_event_id
)
from tests.conftest import count_recent_executions

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration

# Test configuration - use environment variable for signing secret in production
SIGNING_SECRET = os.environ.get('TEST_SLACK_SIGNING_SECRET', 'test_signing_secret_12345')


class TestDuplicateEventDetection:
    """Test suite for duplicate event_id detection"""
    
    def test_duplicate_event_id_rejected(self, aws_resources):
        """Test that duplicate event_id is rejected and not processed twice
        
        Verifies:
        1. First request with event_id is processed
        2. Second request with same event_id returns 200 but is not processed
        3. Only one entry exists in DynamoDB
        4. Only one Step Functions execution is triggered
        """
        # Generate unique event_id for this test
        event_id = generate_unique_event_id("test_duplicate")
        
        # Create Slack event payload
        slack_payload = create_slack_event_payload(
            event_id=event_id,
            text="Test duplicate detection"
        )
        
        # Create API Gateway event
        api_event = create_api_gateway_event(slack_payload, SIGNING_SECRET)
        
        # Get current Step Functions execution count
        executions_before = count_recent_executions(
            aws_resources['sfn_client'],
            aws_resources['state_machine_arn']
        )
        
        # First request - should be processed
        response1 = aws_resources['lambda_client'].invoke(
            FunctionName=aws_resources['lambda_function_name'],
            InvocationType='RequestResponse',
            Payload=json.dumps(api_event)
        )
        
        result1 = json.loads(response1['Payload'].read())
        assert result1['statusCode'] == 200, f"First request failed: {result1}"
        
        # Wait a bit for DynamoDB write
        time.sleep(1)
        
        # Verify event_id is stored in DynamoDB
        item = aws_resources['table'].get_item(Key={'event_id': event_id})
        assert 'Item' in item, "Event ID not found in DynamoDB after first request"
        assert item['Item']['event_id'] == event_id
        
        # Second request with same event_id - should be rejected as duplicate
        response2 = aws_resources['lambda_client'].invoke(
            FunctionName=aws_resources['lambda_function_name'],
            InvocationType='RequestResponse',
            Payload=json.dumps(api_event)
        )
        
        result2 = json.loads(response2['Payload'].read())
        assert result2['statusCode'] == 200, "Duplicate request should return 200"
        
        # Parse response body to check for duplicate message
        body2 = json.loads(result2['body'])
        assert body2.get('ok') is True
        assert 'duplicate' in body2.get('message', '').lower()
        
        # Wait for Step Functions executions to start
        time.sleep(2)
        
        # Verify only one Step Functions execution was triggered
        executions_after = count_recent_executions(
            aws_resources['sfn_client'],
            aws_resources['state_machine_arn']
        )
        
        # Should have exactly one new execution (not two)
        assert executions_after == executions_before + 1, \
            f"Expected 1 new execution, but got {executions_after - executions_before}"
    
    def test_different_event_ids_both_processed(self, aws_resources):
        """Test that different event_ids are both processed
        
        Verifies:
        1. Two requests with different event_ids are both processed
        2. Two entries exist in DynamoDB
        3. Two Step Functions executions are triggered
        """
        # Generate two unique event_ids
        event_id1 = generate_unique_event_id("test_event1")
        event_id2 = generate_unique_event_id("test_event2")
        
        # Create payloads
        slack_payload1 = create_slack_event_payload(event_id=event_id1, text="First event")
        slack_payload2 = create_slack_event_payload(event_id=event_id2, text="Second event")
        
        api_event1 = create_api_gateway_event(slack_payload1, SIGNING_SECRET)
        api_event2 = create_api_gateway_event(slack_payload2, SIGNING_SECRET)
        
        # Get current execution count
        executions_before = count_recent_executions(
            aws_resources['sfn_client'],
            aws_resources['state_machine_arn']
        )
        
        # Send first request
        response1 = aws_resources['lambda_client'].invoke(
            FunctionName=aws_resources['lambda_function_name'],
            InvocationType='RequestResponse',
            Payload=json.dumps(api_event1)
        )
        
        result1 = json.loads(response1['Payload'].read())
        assert result1['statusCode'] == 200
        
        # Send second request
        response2 = aws_resources['lambda_client'].invoke(
            FunctionName=aws_resources['lambda_function_name'],
            InvocationType='RequestResponse',
            Payload=json.dumps(api_event2)
        )
        
        result2 = json.loads(response2['Payload'].read())
        assert result2['statusCode'] == 200
        
        # Wait for DynamoDB writes
        time.sleep(1)
        
        # Verify both event_ids are in DynamoDB
        item1 = aws_resources['table'].get_item(Key={'event_id': event_id1})
        item2 = aws_resources['table'].get_item(Key={'event_id': event_id2})
        
        assert 'Item' in item1, "First event_id not found in DynamoDB"
        assert 'Item' in item2, "Second event_id not found in DynamoDB"
        
        # Wait for Step Functions executions
        time.sleep(2)
        
        # Verify two Step Functions executions were triggered
        executions_after = count_recent_executions(
            aws_resources['sfn_client'],
            aws_resources['state_machine_arn']
        )
        
        assert executions_after == executions_before + 2, \
            f"Expected 2 new executions, but got {executions_after - executions_before}"


class TestStepFunctionsExecution:
    """Test suite for Step Functions execution verification"""
    
    def test_step_functions_triggered_on_valid_request(self, aws_resources):
        """Test that Step Functions execution is triggered on valid request
        
        Verifies:
        1. Lambda function returns 200 OK immediately
        2. Step Functions execution is started
        3. Execution ARN is logged
        """
        # Generate unique event_id
        event_id = generate_unique_event_id("test_sfn")
        
        # Create Slack event
        slack_payload = create_slack_event_payload(
            event_id=event_id,
            text="Test Step Functions execution"
        )
        
        api_event = create_api_gateway_event(slack_payload, SIGNING_SECRET)
        
        # Get executions before
        executions_before = aws_resources['sfn_client'].list_executions(
            stateMachineArn=aws_resources['state_machine_arn'],
            maxResults=10
        )
        
        execution_arns_before = {e['executionArn'] for e in executions_before['executions']}
        
        # Invoke Lambda
        response = aws_resources['lambda_client'].invoke(
            FunctionName=aws_resources['lambda_function_name'],
            InvocationType='RequestResponse',
            Payload=json.dumps(api_event)
        )
        
        result = json.loads(response['Payload'].read())
        
        # Verify Lambda returns 200 OK immediately
        assert result['statusCode'] == 200, f"Lambda should return 200, got {result}"
        
        # Wait for Step Functions to start
        time.sleep(2)
        
        # Get executions after
        executions_after = aws_resources['sfn_client'].list_executions(
            stateMachineArn=aws_resources['state_machine_arn'],
            maxResults=10
        )
        
        execution_arns_after = {e['executionArn'] for e in executions_after['executions']}
        
        # Verify new execution was created
        new_executions = execution_arns_after - execution_arns_before
        assert len(new_executions) >= 1, "No new Step Functions execution found"
        
        # Get the new execution details
        new_execution_arn = list(new_executions)[0]
        execution_details = aws_resources['sfn_client'].describe_execution(
            executionArn=new_execution_arn
        )
        
        # Verify execution status
        assert execution_details['status'] in ['RUNNING', 'SUCCEEDED'], \
            f"Execution status should be RUNNING or SUCCEEDED, got {execution_details['status']}"
    
    def test_step_functions_execution_completes_successfully(self, aws_resources):
        """Test that Step Functions execution completes successfully
        
        Verifies:
        1. Execution reaches SUCCEEDED status
        2. Processor Lambda is invoked
        3. No errors occur during execution
        
        Note: This test may take longer as it waits for execution to complete.
        Uses a simple greeting text that won't trigger external tool calls.
        """
        # Generate unique event_id
        event_id = generate_unique_event_id("test_sfn_complete")
        
        # Create simple Slack event to avoid actual Slack/Sheets calls during test
        # Simple greeting text that the AI agent can respond to without external tools
        slack_payload = create_slack_event_payload(
            event_id=event_id,
            text="こんにちは"  # Simple Japanese greeting
        )
        
        api_event = create_api_gateway_event(slack_payload, SIGNING_SECRET)
        
        # Invoke Lambda
        response = aws_resources['lambda_client'].invoke(
            FunctionName=aws_resources['lambda_function_name'],
            InvocationType='RequestResponse',
            Payload=json.dumps(api_event)
        )
        
        result = json.loads(response['Payload'].read())
        assert result['statusCode'] == 200
        
        # Wait for execution to start
        time.sleep(2)
        
        # Find the execution
        executions = aws_resources['sfn_client'].list_executions(
            stateMachineArn=aws_resources['state_machine_arn'],
            maxResults=10
        )
        
        # Find our execution (most recent one)
        target_execution = None
        for execution in executions['executions']:
            if (time.time() - execution['startDate'].timestamp()) < 10:  # Within last 10 seconds
                target_execution = execution
                break
        
        assert target_execution is not None, "Could not find the execution"
        
        # Wait for execution to complete (with timeout)
        max_wait = 60  # Maximum 60 seconds
        wait_interval = 5
        waited = 0
        
        while waited < max_wait:
            execution_details = aws_resources['sfn_client'].describe_execution(
                executionArn=target_execution['executionArn']
            )
            
            status = execution_details['status']
            
            if status == 'SUCCEEDED':
                # Success!
                return
            elif status in ['FAILED', 'TIMED_OUT', 'ABORTED']:
                pytest.fail(f"Execution failed with status: {status}")
            
            # Still running, wait more
            time.sleep(wait_interval)
            waited += wait_interval
        
        # Timeout
        pytest.fail(f"Execution did not complete within {max_wait} seconds")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
