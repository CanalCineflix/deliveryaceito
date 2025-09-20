#!/usr/bin/env bash

# Sair imediatamente se um comando falhar
set -o errexit

# Define a variável de ambiente PYTHONPATH para incluir o diretório src
export PYTHONPATH=/opt/render/project/src:$PYTHONPATH

# Instala as dependências do projeto usando pip
pip install -r requirements.txt

# Limpa o banco de dados. Isso pode ser agressivo.
# Se você quiser manter os dados em deploys subsequentes, remova esta linha.
psql $DATABASE_URL -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# Remove o diretório de migrações (se existir) para evitar conflitos de histórico
rm -rf migrations

# Inicia as migrações, cria a pasta 'migrations'
flask db init

# Cria a migração inicial (se houver alterações nos modelos)
flask db migrate -m "Initial migration"

# Aplica as migrações no banco de dados.
flask db upgrade

# Roda o comando para criar os planos no banco de dados.
# Esta é a etapa crucial que popula a URL de checkout.
flask create_plans
