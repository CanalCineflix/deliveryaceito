#!/usr/bin/env bash

Exit immediately if a command exits with a non-zero status.
set -o errexit

Install dependencies from requirements.txt
pip install -r requirements.txt

Apply all pending database migrations to the latest revision.
This is the best practice for production environments.
flask db upgrade