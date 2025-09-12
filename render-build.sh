#!/usr/bin/env bash

Exit on first error
set -o errexit

Install dependencies from requirements.txt
pip install -r requirements.txt

Fix database migration history inconsistency and apply all pending changes.
This is the best practice for production environments like Render.
flask db stamp head
flask db migrate -m "Sincroniza migrações com o modelo mais recente"
flask db upgrade
