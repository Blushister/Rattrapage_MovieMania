#!/bin/bash
set -e

echo "🚀 Starting Users API with clean startup..."

# Install mysql-connector-python for the cleanup script
pip install mysql-connector-python

# Run the cleanup script
python /app/clear-users-startup.py

# Start the API
echo "🎯 Starting Users API server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8888 --log-level debug --access-log