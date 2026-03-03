#!/bin/bash

echo "🧪 Testing AI Production Debugger locally..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found"
    exit 1
fi

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Set environment variables
export LLM_PROVIDER=mock
export KUBECONFIG=~/.kube/config

# Run the app
echo "🚀 Starting server..."
echo "📡 API will be available at http://localhost:8000"
echo "🔍 Test with: curl http://localhost:8000/health"
echo ""
python3 -m uvicorn ai_debugger.api.main:app --reload --host 0.0.0.0 --port 8000
