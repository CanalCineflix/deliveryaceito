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

# **CRÍTICO:** Marca o banco de dados como "atualizado". Isso sincroniza o histórico local
# com o banco de dados remoto, resolvendo o erro de revisão não encontrada.
flask db stamp head

# Aplica as migrações no banco de dados.
# Isso garante que qualquer alteração no modelo seja refletida no DB.
flask db upgrade

# Você pode rodar outros scripts de setup aqui se precisar
# Exemplo: python create_plans.py
