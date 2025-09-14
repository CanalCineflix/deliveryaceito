#!/usr/bin/env bash

Exit immediately if a command fails
set -o errexit

Change to the 'src' directory
cd /opt/render/project/src

Install project dependencies using pip
pip install -r requirements.txt

CRITICAL: Completely wipes the database, deleting all tables.
This ensures there will be no conflicts with old migrations.
psql $DATABASE_URL -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

Remove the migrations directory to avoid history conflicts
rm -rf migrations

Create the initial Alembic migrations structure.
flask db init

Create the initial migration based on current models.
flask db migrate -m "Initial migration"

Apply migrations to the now-clean database.
flask db upgrade

Run the script to create initial plans in the database
python create_plans.py
