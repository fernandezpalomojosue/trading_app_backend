#!/bin/bash
set -e

echo "Starting DB migration..."

# solo ejecutar en la instancia leader (truco simple)
if [ "$EB_IS_COMMAND_LEADER" != "true" ]; then
  echo "Not leader instance, skipping migrations."
  exit 0
fi

source /var/app/venv/*/bin/activate
cd /var/app/current

python scripts/render_migrate.py

echo "Migration completed."