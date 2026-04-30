#!/bin/bash
# AWS Elastic Beanstalk predeploy hook
# Runs database migrations before deploying new version

set -e

echo "=========================================="
echo "🔄 Running database migrations (AWS EB)"
echo "=========================================="

# Check if we're in the right directory
cd /var/app/staging

# Activate virtual environment if it exists
if [ -d /var/app/venv ]; then
    source /var/app/venv/bin/activate
elif [ -d /var/app/staging/venv ]; then
    source /var/app/staging/venv/bin/activate
fi

# Run migrations using the render_migrate.py script
python scripts/render_migrate.py

if [ $? -eq 0 ]; then
    echo "✅ Migrations completed successfully!"
else
    echo "❌ Migration failed!"
    exit 1
fi

echo "=========================================="
