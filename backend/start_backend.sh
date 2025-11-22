#!/bin/bash

# Script to start the backend server

echo "Starting Athletic Spirit AI Coach Backend..."

# Check if required packages are installed
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "Installing required packages..."
    pip3 install -r requirements.txt
fi

# Start the FastAPI server
echo "Starting server on http://127.0.0.1:8000"
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
