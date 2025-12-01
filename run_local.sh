#!/bin/bash

# Local testing script for My Meal Planner
# This script sets up and runs the backend server locally

echo "🚀 Starting My Meal Planner Backend (Local)"
echo "============================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r mymealplanner/requirements.txt

# Check for required environment variables
if [ -z "$GOOGLE_CLOUD_PROJECT" ]; then
    echo ""
    echo "⚠️  WARNING: GOOGLE_CLOUD_PROJECT not set!"
    echo "   Please set it with: export GOOGLE_CLOUD_PROJECT=your-project-id"
    echo ""
    read -p "Enter your Google Cloud Project ID: " project_id
    export GOOGLE_CLOUD_PROJECT=$project_id
fi

if [ -z "$GOOGLE_CLOUD_LOCATION" ]; then
    export GOOGLE_CLOUD_LOCATION=us-central1
    echo "📍 Using default location: us-central1"
fi

echo ""
echo "✅ Starting server on http://localhost:8080"
echo "   Frontend: Open index.html in your browser"
echo "   Press Ctrl+C to stop"
echo ""

# Run the server
python main.py

