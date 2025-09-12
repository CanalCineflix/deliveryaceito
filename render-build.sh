#!/usr/bin/env bash

Exit on first error
set -o errexit

Install dependencies from requirements.txt
pip install -r requirements.txt

Corrige o problema de inconsistência de histórico de migrações
e aplica todas as mudanças pendentes ao banco de dados.
Esta é a melhor prática para ambientes de produção como o Render.
flask db stamp head
flask db migrate -m "Sincroniza migrações com o modelo mais recente"
flask db upgrade
