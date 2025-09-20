#!/usr/bin/env bash

# Sair imediatamente se um comando falhar
set -o errexit

# Define a variável de ambiente PYTHONPATH para incluir o diretório src
export PYTHONPATH=/opt/render/project/src:$PYTHONPATH

# Define a variável FLASK_APP para que o Flask encontre a sua aplicação
export FLASK_APP=run.py

# Instala as dependências do projeto usando pip
pip install -r requirements.txt

# Limpa o banco de dados completamente.
psql $DATABASE_URL -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# Remove o diretório de migrações (importante para recriar as tabelas corretamente)
rm -rf migrations

# Inicia as migrações
flask db init

# Cria uma nova migração com as alterações dos modelos (incluindo is_free)
flask db migrate -m "Added is_free to Plan model"

# Aplica as migrações no banco de dados.
flask db upgrade

# Roda o comando para criar os planos iniciais no banco de dados.
flask create_plans
