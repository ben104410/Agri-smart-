#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Collect static files into staticfiles/ for WhiteNoise
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate

# Optionally seed demonstration data if requested
if [ "$SEED_DEMO_DATA" = "true" ]; then
    python manage.py seed_demo_data
fi
