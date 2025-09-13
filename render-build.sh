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

# Cria uma nova migração autogerada
flask db migrate -m "Sincronizando banco de dados com os modelos atuais"

# Marca o banco de dados como atualizado para a revisão mais recente
flask db stamp head

# Aplica as migrações no banco de dados
flask db upgrade

# Você pode rodar outros scripts de setup aqui se precisar
# Exemplo: python create_plans.py
