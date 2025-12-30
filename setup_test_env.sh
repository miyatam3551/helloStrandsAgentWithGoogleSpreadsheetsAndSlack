#!/bin/bash
# Setup script for integration tests
# This script extracts Terraform outputs and sets environment variables

set -euo pipefail  # Exit on error, undefined variables, and pipe failures

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up integration test environment...${NC}"

# Check if terraform directory exists
if [ ! -d "terraform" ]; then
    echo -e "${RED}Error: terraform directory not found${NC}"
    echo "Please run this script from the project root"
    exit 1
fi

# Change to terraform directory
cd terraform

# Check if terraform is initialized
if [ ! -d ".terraform" ]; then
    echo -e "${YELLOW}Terraform not initialized. Running terraform init...${NC}"
    terraform init
fi

# Get Terraform outputs
echo -e "${GREEN}Retrieving Terraform outputs...${NC}"

DYNAMODB_TABLE_NAME=$(terraform output -raw dynamodb_table_name 2>/dev/null || echo "")
STATE_MACHINE_ARN=$(terraform output -raw state_machine_arn 2>/dev/null || echo "")
LAMBDA_FUNCTION_NAME=$(terraform output -raw lambda_function_name 2>/dev/null || echo "")

# Check if outputs are available
if [ -z "$DYNAMODB_TABLE_NAME" ] || [ -z "$STATE_MACHINE_ARN" ] || [ -z "$LAMBDA_FUNCTION_NAME" ]; then
    echo -e "${RED}Error: Could not retrieve Terraform outputs${NC}"
    echo "Please make sure you have run 'terraform apply' first"
    exit 1
fi

# Change back to project root
cd ..

# Create .env file for tests
ENV_FILE="tests/.env"
echo -e "${GREEN}Creating ${ENV_FILE}...${NC}"

cat > "$ENV_FILE" << EOF
# Auto-generated environment variables for integration tests
# Generated at: $(date)

# DynamoDB table name for event deduplication
DYNAMODB_TABLE_NAME=${DYNAMODB_TABLE_NAME}

# Step Functions state machine ARN
STATE_MACHINE_ARN=${STATE_MACHINE_ARN}

# Lambda function name (receiver)
LAMBDA_FUNCTION_NAME=${LAMBDA_FUNCTION_NAME}

# AWS region
AWS_REGION=${AWS_REGION:-ap-northeast-1}
EOF

echo -e "${GREEN}✅ Environment file created successfully${NC}"
echo ""
echo -e "${YELLOW}Environment variables:${NC}"
echo "  DYNAMODB_TABLE_NAME=${DYNAMODB_TABLE_NAME}"
echo "  STATE_MACHINE_ARN=${STATE_MACHINE_ARN}"
echo "  LAMBDA_FUNCTION_NAME=${LAMBDA_FUNCTION_NAME}"
echo "  AWS_REGION=${AWS_REGION:-ap-northeast-1}"
echo ""
echo -e "${GREEN}You can now run the integration tests:${NC}"
echo "  pytest tests/integration/ -v"
