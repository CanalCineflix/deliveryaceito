#!/usr/bin/env bash

Sair imediatamente se um comando falhar
set -o errexit

Entrar no diretório da aplicação
cd /opt/render/project/src

Instalar as dependências do Python
pip install -r requirements.txt

Inicializar o diretório de migrações se ele não existir
if [ ! -d "migrations" ]; then
echo "Diretório de migrações não encontrado. Inicializando..."
flask db init
fi

Aplicar as migrações automáticas do banco de dados
echo "Aplicando migrações automáticas..."
flask db migrate --autogenerate -m "Aplicação de migrações automáticas"

Executar todas as migrações pendentes
echo "Executando upgrade do banco de dados..."
flask db upgrade

Executar o script de criação de planos
echo "Criando planos no banco de dados..."
python create_plans.py
