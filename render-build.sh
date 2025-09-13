#!/usr/bin/env bash

# Sair imediatamente se um comando falhar
set -o errexit

# Entra no diretório 'src' onde o pyproject.toml deve estar
cd /opt/render/project/src

# Definir a variável de ambiente para que o Poetry não crie o ambiente virtual
# dentro do diretório do projeto, pois o Render já faz isso.
export POETRY_VIRTUALENVS_IN_PROJECT=false

# Instalar as dependências do projeto
poetry install --no-dev

# Coletar os arquivos estáticos para o Gunicorn
python manage.py collectstatic --noinput

# Executar as migrações do banco de dados
python manage.py migrate
