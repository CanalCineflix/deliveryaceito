#!/usr/bin/env bash

Sair imediatamente se um comando falhar
set -o errexit

Entra no diretório 'src'
cd /opt/render/project/src

Instala as dependências do projeto usando pip
pip install -r requirements.txt

Cria a estrutura inicial de migrações do Alembic se ela não existir
Isso é seguro para rodar múltiplas vezes
flask db init || true

Cria uma nova migração com base nas mudanças nos modelos
A flag '--autogenerate' automatiza a detecção de alterações
flask db migrate --autogenerate -m "Aplicação de migrações automáticas"

Aplica as migrações pendentes no banco de dados
flask db upgrade

Roda o script para criar os planos iniciais no banco de dados, se necessário
python create_plans.py
