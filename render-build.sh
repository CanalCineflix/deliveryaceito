#!/usr/bin/env bash

Exit immediately if a command exits with a non-zero status.
set -o errexit

Change to the application directory
cd /opt/render/project/src

Install Python dependencies
pip install -r requirements.txt

Initialize the migrations directory if it doesn't exist
if [ ! -d "migrations" ]; then
echo "Migrations directory not found. Initializing..."
flask db init
fi

Apply automatic database migrations
echo "Applying automatic migrations..."
flask db migrate --autogenerate -m "Aplicação de migrações automáticas"

Run all pending migrations
echo "Executing database upgrade..."
flask db upgrade

Run the create plans script
echo "Creating plans in the database..."
python create_plans.py
