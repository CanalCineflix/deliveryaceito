#!/usr/bin/env bash

# Sair imediatamente se um comando falhar
set -o errexit

# Entra no diretório 'src'
cd /opt/render/project/src

# Instala as dependências do projeto usando pip
pip install -r requirements.txt

# Executa o script de migrações
python run_migrations.py

# Você pode rodar outros scripts de setup aqui se precisar
# Exemplo: python create_plans.py
