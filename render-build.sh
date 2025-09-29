#!/usr/bin/env bash

# Sair imediatamente se um comando falhar
set -o errexit

# Define a variável de ambiente PYTHONPATH para que o Python encontre os módulos
export PYTHONPATH=/opt/render/project/src:$PYTHONPATH

# IMPORTANTE: A variável FLASK_APP deve ser definida no painel do Render!
# Se for definida apenas aqui, ela não persiste para o "Start Command".
# export FLASK_APP=run.py <-- REMOVA ESTA LINHA E COLOQUE NO PAINEL DO RENDER

# Instala as dependências
pip install -r requirements.txt

# REMOVER COMANDOS DE BANCO DE DADOS DE BUILD TIME!
# NUNCA execute comandos que alteram o banco de dados (como DROP SCHEMA, rm -rf migrations, 
# db init/migrate/upgrade/create_plans) durante a fase de build. 
# Eles devem ser executados APENAS durante a fase de START pelo comando 'flask deploy'.

# O Build é apenas para instalar o código.
echo "Build completo. Migrações serão aplicadas no Start Command."
