#!/usr/bin/env bash
# Render build step for the backend. Runs on every deploy.
set -o errexit

pip install -r requirements.txt

# Collect static assets for WhiteNoise (Django admin, DRF browsable API).
python manage.py collectstatic --no-input

# Apply migrations and (idempotently) seed demo users/documents so reviewers
# can log in and exercise the sharing flow immediately.
python manage.py migrate
python manage.py seed
