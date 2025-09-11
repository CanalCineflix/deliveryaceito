#!/usr/bin/env bash

Exit on first error
set -o errexit

Install dependencies from requirements.txt
pip install -r requirements.txt

Create tables directly from models in a separate script
python create_db.py
