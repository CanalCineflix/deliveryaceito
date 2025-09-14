

#!/usr/bin/env bash

# Sair imediatamente se um comando falhar
set -o errexit

# Entra no diretório 'src'
cd /opt/render/project/src

# Instala as dependências do projeto usando pip
pip install -r requirements.txt

# **CRÍTICO:** Limpa completamente o banco de dados, apagando todas as tabelas.
# Isso garante que não haverá conflitos com migrações antigas.
psql $DATABASE_URL -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# Remove o diretório de migrações para evitar conflitos de histórico
rm -rf migrations

# Cria a estrutura inicial de migrações do Alembic.
flask db init

# Cria a migração inicial com base nos modelos atuais.
flask db migrate -m "Initial migration"

# Aplica as migrações no banco de dados agora limpo.
flask db upgrade

# Roda o script para criar os planos iniciais no banco de dados
python create_plans.py
