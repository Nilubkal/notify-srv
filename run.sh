#!/bin/bash
#
# Simple script to run the notification service
# Uses uv for fast dependency management

set -e

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "ERROR: uv is not installed"
    echo "       Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "       Or with homebrew: brew install uv"
    exit 1
fi

# Check if venv exists
if [ ! -d ".venv" ]; then
    echo "ERROR: Virtual environment not found"
    echo "       Create it first with: uv venv"
    exit 1
fi

# Activate existing venv and install dependencies with uv
echo "Setting up environment with uv..."
source .venv/bin/activate
uv pip install -r requirements.txt

# Run the service
echo ""
echo "🚀 Starting Notification Service..."
echo "   API: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
echo ""

uvicorn main:app --reload --host 0.0.0.0 --port 8000