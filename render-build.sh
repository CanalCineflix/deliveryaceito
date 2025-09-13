#!/usr/bin/env bash

# Sair imediatamente se um comando falhar
set -o errexit

# Entra no diretório 'src'
cd /opt/render/project/src

# Instala as dependências do projeto usando pip
pip install -r requirements.txt

# Remove o diretório de migrações para evitar conflitos de histórico
rm -rf migrations

# Cria um novo diretório de migrações.
# Isso não cria a tabela, apenas a estrutura.
flask db init

# **CRÍTICO:** Cria a migração inicial com base nos modelos atuais.
# Este comando gera o arquivo .py que o Alembic usará para criar as tabelas.
flask db migrate -m "Initial migration"

# Aplica as migrações no banco de dados.
# Agora, haverá um arquivo para o Alembic aplicar, resolvendo o erro anterior.
flask db upgrade

# Roda o script para criar os planos iniciais no banco de dados
python create_plans.py
