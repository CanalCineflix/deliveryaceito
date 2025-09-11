#!/usr/bin/env bash

Exit on first error
set -o errexit

Install dependencies from requirements.txt
pip install -r requirements.txt

Create tables directly from models
python -c "from app import create_app; from extensions import db; app = create_app(); with app.app_context(): db.create_all()"
