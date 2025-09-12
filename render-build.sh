#!/usr/bin/env bash

set -o errexit

pip install -r requirements.txt

flask db stamp head
flask db migrate -m "Sincroniza migrações com o modelo mais recente"
flask db upgrade
