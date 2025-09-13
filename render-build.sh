#!/usr/bin/env bash

# Sair imediatamente se um comando falhar
set -o errexit

# Entra no diretório 'src' onde o pyproject.toml deve estar
# Embora pyproject.toml não exista, é uma boa prática
# manter o cd para a raiz do projeto.
cd /opt/render/project/src

# Instalar as dependências do projeto usando pip
pip install -r requirements.txt

# Coletar os arquivos estáticos para o Gunicorn
python manage.py collectstatic --noinput

# Executar as migrações do banco de dados
python manage.py migrate
