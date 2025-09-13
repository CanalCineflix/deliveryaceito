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

# Sincroniza o banco de dados com os modelos atuais, criando uma nova migração
flask db migrate -m "Sincronizando banco de dados com os modelos atuais"

# Aplica as migrações no banco de dados
flask db upgrade

# Você pode rodar outros scripts de setup aqui se precisar
# Exemplo: python create_plans.py
