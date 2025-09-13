#!/usr/bin/env bash

# Sair imediatamente se um comando falhar
set -o errexit

# Entra no diretório 'src' para garantir o caminho correto
cd /opt/render/project/src

# Instala as dependências do projeto listadas em requirements.txt
pip install -r requirements.txt
