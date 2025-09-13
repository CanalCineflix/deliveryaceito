#!/usr/bin/env bash

# Sair imediatamente se um comando falhar
set -o errexit

# Entra no diretório 'src'
cd /opt/render/project/src

# Instala as dependências do projeto usando pip
pip install -r requirements.txt

# Remove o diretório de migrações para evitar conflitos de histórico
rm -rf migrations

# Cria um novo diretório de migrações.
# Isso não cria a tabela, apenas a estrutura.
flask db init

# **CRÍTICO:** Marca o banco de dados como "atualizado" com o head.
# Isso sincroniza o histórico remoto com o local, resolvendo o erro de revisão.
flask db stamp head

# Aplica as migrações no banco de dados.
# Este passo agora deve ser bem-sucedido, pois o banco de dados
# está sincronizado com a versão mais recente do seu código.
flask db upgrade

# Roda o script para criar os planos iniciais no banco de dados
python create_plans.py
