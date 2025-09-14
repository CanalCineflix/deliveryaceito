#!/usr/bin/env bash
set -o errexit
cd /opt/render/project/src
pip install -r requirements.txt
flask db init
flask db migrate --autogenerate -m "Aplicação de migrações automáticas"
flask db upgrade
python create_plans.py
