#!/usr/bin/env bash

set -o errexit

export PYTHONPATH=/opt/render/project/src:$PYTHONPATH

export FLASK_APP=run.py

pip install -r requirements.txt

psql $DATABASE_URL -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

rm -rf migrations

flask db init

flask db migrate -m "Added is_free column to Plan model"

flask db upgrade

flask create_plans
