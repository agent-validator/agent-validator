#!/bin/bash
# Smoke test runner script for agent-validator library and CLI

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Agent Validator Library & CLI Smoke Tests${NC}"
echo "================================================"

# Check if we're in the right directory
if [ ! -f "smoke_tests.py" ]; then
    echo -e "${RED}❌ Error: smoke_tests.py not found in current directory${NC}"
    echo "Please run this script from the smoke_tests/ directory"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Error: python3 not found${NC}"
    exit 1
fi

echo -e "${BLUE}🔧 Configuration:${NC}"
echo "  Python: $(python3 --version)"
echo "  Directory: $(pwd)"
echo ""

# Create isolated virtual environment for smoke tests
echo -e "${BLUE}🔍 Creating isolated virtual environment...${NC}"
VENV_DIR="smoke_test_env"
rm -rf "$VENV_DIR"
python3 -m venv "$VENV_DIR"

# Activate virtual environment
echo -e "${BLUE}🔍 Activating virtual environment...${NC}"
source "$VENV_DIR/bin/activate"

# Install package in isolated environment
echo -e "${BLUE}🔍 Installing agent-validator in isolated environment...${NC}"
pip install -e "../.[dev]"

# Verify installation
if ! python -c "import agent_validator" 2>/dev/null; then
    echo -e "${RED}❌ Failed to install agent-validator in virtual environment${NC}"
    exit 1
fi

if ! command -v agent-validator &> /dev/null; then
    echo -e "${RED}❌ CLI not available in virtual environment${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Package installed in isolated environment${NC}"
echo -e "${GREEN}✅ CLI available: $(which agent-validator)${NC}"

echo ""
echo -e "${BLUE}🧪 Running smoke tests...${NC}"
echo ""

# Run the smoke tests in isolated environment
echo -e "${BLUE}🧪 Running smoke tests in isolated environment...${NC}"
python smoke_tests.py

# Capture exit code
EXIT_CODE=$?

# Deactivate virtual environment
deactivate

# Clean up virtual environment
echo -e "${BLUE}🧹 Cleaning up isolated environment...${NC}"
rm -rf "$VENV_DIR"

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}🎉 All smoke tests passed!${NC}"
    echo ""
    echo -e "${BLUE}📋 What was tested:${NC}"
    echo "  ✅ CLI help and commands"
    echo "  ✅ ID generation"
    echo "  ✅ Configuration management"
    echo "  ✅ Validation (success and failure cases)"
    echo "  ✅ Log viewing (local and cloud)"
    echo "  ✅ Library imports and functionality"
    echo "  ✅ Validation modes (strict and coerce)"
    echo "  ✅ Error handling"
    echo "  ✅ Configuration system"
    echo "  ✅ Retry logic"
    echo "  ✅ Logging functionality"
    echo ""
    echo -e "${BLUE}🔒 Tests ran in isolated environment - no pollution to your dev environment${NC}"
else
    echo -e "${RED}❌ Some smoke tests failed${NC}"
fi

exit $EXIT_CODE
