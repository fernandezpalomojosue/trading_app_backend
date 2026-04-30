#!/bin/bash
# AWS Elastic Beanstalk predeploy hook
# Runs database migrations before deploying new version

set -e

echo "=========================================="
echo "🔄 Running database migrations (AWS EB)"
echo "=========================================="

# Check if we're in the right directory
cd /var/app/staging

# Find and activate virtual environment
# EB Python platform can have venv in different locations
if [ -f /var/app/venv/bin/activate ]; then
    echo "📦 Activating venv at /var/app/venv"
    source /var/app/venv/bin/activate
elif [ -f /var/app/staging/venv/bin/activate ]; then
    echo "📦 Activating venv at /var/app/staging/venv"
    source /var/app/staging/venv/bin/activate
elif [ -f venv/bin/activate ]; then
    echo "📦 Activating venv at ./venv"
    source venv/bin/activate
elif [ -f /opt/python/run/venv/bin/activate ]; then
    echo "📦 Activating venv at /opt/python/run/venv"
    source /opt/python/run/venv/bin/activate
else
    echo "⚠️  No virtual environment found, using system Python"
fi

# Debug: Show Python path and version
echo "🐍 Python: $(which python)"
echo "📋 Python version: $(python --version)"

# Run migrations using the render_migrate.py script
echo "🚀 Running migrations..."
python scripts/render_migrate.py

if [ $? -eq 0 ]; then
    echo "✅ Migrations completed successfully!"
else
    echo "❌ Migration failed!"
    exit 1
fi

echo "=========================================="
