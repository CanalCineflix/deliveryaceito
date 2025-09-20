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
# Nota: Esta linha apaga todos os dados, use com cautela.
psql $DATABASE_URL -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# Remove o diretório de migrações para evitar conflitos de histórico
rm -rf migrations

# Inicia as migrações, criando a pasta 'migrations'
flask db init

# Cria a migração inicial com base nos modelos atuais.
flask db migrate -m "Initial migration"

# Aplica as migrações no banco de dados.
flask db upgrade

# Roda o comando para criar os planos iniciais no banco de dados.
# Agora o Flask vai reconhecer o comando 'create_plans'.
flask create_plans
