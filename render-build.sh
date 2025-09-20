#!/usr/bin/env bash

# Sair imediatamente se um comando falhar
set -o errexit

# Define a variável de ambiente PYTHONPATH para que o Python encontre os módulos
export PYTHONPATH=/opt/render/project/src:$PYTHONPATH

# Define a variável FLASK_APP para que o Flask encontre a sua aplicação
export FLASK_APP=run.py

# Instala as dependências
pip install -r requirements.txt

# Limpa o banco de dados para uma nova inicialização
psql $DATABASE_URL -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# Remove o diretório de migrações (importante para evitar histórico conflitante)
rm -rf migrations

# Inicia as migrações (cria a pasta 'migrations')
flask db init

# Cria a migração inicial com base nos modelos atuais (agora com 'is_free')
flask db migrate -m "Added is_free to Plan model"

# Aplica as migrações no banco de dados
flask db upgrade

# Roda o comando para criar os planos (agora, ele não vai falhar)
flask create_plans
