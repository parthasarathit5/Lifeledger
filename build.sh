#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "Installing Python ML & Django requirements..."
pip install -r requirements.txt

echo "Generating ML Datasets & Training AI Models..."
python ml_engine/generate_dataset.py
python ml_engine/train_models.py

echo "Collecting static assets..."
python manage.py collectstatic --no-input

echo "Applying Supabase database migrations..."
python manage.py migrate

echo "LifeLedger AI Backend Build Complete!"
