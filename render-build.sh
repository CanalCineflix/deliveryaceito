#!/usr/bin/env bash

Exit immediately if a command fails
set -o errexit

Enter the 'src' directory
cd /opt/render/project/src

Install project dependencies using pip
pip install -r requirements.txt

Create the initial Alembic migration structure if it doesn't exist
This is safe to run multiple times
flask db init || true

Create a new migration based on model changes
The '--autogenerate' flag automates the detection of changes
flask db migrate --autogenerate -m "Aplicação de migrações automáticas"

Apply the pending database migrations
flask db upgrade

Run the script to create initial plans in the database, if necessary
python create_plans.py
