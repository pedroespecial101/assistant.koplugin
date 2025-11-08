#!/bin/bash
#
# Quick start script for the companion app
#

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "======================================"
echo "KOReader AI Companion - Quick Start"
echo "======================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not found"
    echo "   Install it from https://www.python.org/"
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"

# Check/install dependencies
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    
    echo "📦 Installing dependencies..."
    source venv/bin/activate
    pip install --quiet -r requirements.txt
    
    echo "✓ Dependencies installed"
else
    echo "✓ Virtual environment exists"
    source venv/bin/activate
fi

echo ""
echo "======================================"
echo "Starting Companion Server"
echo "======================================"
echo ""
echo "📱 Kindle endpoint: http://192.168.1.102:8080"
echo "🌐 Dashboard: http://localhost:8080"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python3 companion/app.py
