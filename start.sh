#!/bin/bash
# Development Automation Suite Launcher for Unix/Linux/macOS
# This script helps launch the application with proper error handling

echo
echo "============================================================"
echo "     Development Automation Suite - Unix/Linux Launcher"
echo "============================================================"
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo -e "${RED}❌ Python is not installed or not in PATH${NC}"
        echo
        echo "Please install Python 3.8+ from your package manager:"
        echo "  Ubuntu/Debian: sudo apt install python3 python3-pip"
        echo "  CentOS/RHEL:   sudo yum install python3 python3-pip"
        echo "  macOS:         brew install python3"
        echo "  Or visit:      https://www.python.org/downloads/"
        echo
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

echo -e "${GREEN}✅ Python found${NC}"
echo

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
if [[ $(echo "$PYTHON_VERSION < 3.8" | bc -l) -eq 1 ]]; then
    echo -e "${RED}❌ Python 3.8+ is required (found $PYTHON_VERSION)${NC}"
    echo "Please upgrade your Python installation"
    exit 1
fi

echo -e "${BLUE}🐍 Python version: $PYTHON_VERSION${NC}"

# Check if we're in a virtual environment
if [[ -n "$VIRTUAL_ENV" ]]; then
    echo -e "${GREEN}🐍 Virtual environment active: $VIRTUAL_ENV${NC}"
else
    echo -e "${YELLOW}💡 Consider using a virtual environment:${NC}"
    echo "   python3 -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
fi
echo

# Check if requirements.txt exists
if [[ -f "requirements.txt" ]]; then
    echo -e "${BLUE}📦 Installing/updating dependencies...${NC}"
    $PYTHON_CMD -m pip install -r requirements.txt
    echo
else
    echo -e "${YELLOW}⚠️  No requirements.txt found, proceeding anyway...${NC}"
    echo
fi

# Make run.py executable if needed
if [[ ! -x "run.py" ]]; then
    chmod +x run.py
fi

# Launch the application
echo -e "${GREEN}🚀 Starting Development Automation Suite...${NC}"
$PYTHON_CMD run.py

exit_code=$?
if [[ $exit_code -ne 0 ]]; then
    echo
    echo -e "${RED}❌ Application failed to start (exit code: $exit_code)${NC}"
    echo "Check the error messages above for details"
    echo
    exit $exit_code
fi

echo
echo -e "${GREEN}👋 Application closed successfully${NC}" 