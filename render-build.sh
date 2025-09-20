#!/usr/bin/env bash

# Sair imediatamente se um comando falhar
set -o errexit

# Define a variável de ambiente PYTHONPATH para incluir o diretório src
# Isso permite que o Python encontre o pacote 'rotas'
export PYTHONPATH=/opt/render/project/src:$PYTHONPATH

# Instala as dependências do projeto usando pip
pip install -r requirements.txt

# Limpa completamente o banco de dados.
# Isso garante que não haverá conflitos com migrações antigas.
psql $DATABASE_URL -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# Remove o diretório de migrações para evitar conflitos de histórico
rm -rf migrations

# Inicia as migrações, criando a pasta 'migrations'
flask db init

# Cria a migração inicial com base nos modelos atuais.
flask db migrate -m "Initial migration"

# Aplica as migrações no banco de dados.
flask db upgrade

# Roda o script para criar os planos iniciais no banco de dados
python create_plans.py

pip install Flask-Click
flask create_plans
