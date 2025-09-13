#!/usr/bin/env bash

# Sair imediatamente se um comando falhar
set -o errexit

# Entra no diretório 'src'
cd /opt/render/project/src

# Instala as dependências do projeto usando pip
pip install -r requirements.txt

# Remove o diretório de migrações para evitar conflitos de histórico
rm -rf migrations

# Cria um novo diretório de migrações
flask db init

# Cria a migração inicial com base nos modelos atuais.
# Este é o passo crucial que estava faltando.
flask db migrate -m "Initial migration"

# Aplica as migrações no banco de dados.
# Agora, haverá um arquivo para o Alembic aplicar.
flask db upgrade

# Você pode rodar outros scripts de setup aqui se precisar
# Exemplo: python create_plans.py
