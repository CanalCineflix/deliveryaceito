#!/usr/bin/env bash

# Sair imediatamente se um comando falhar
set -o errexit

# Entra no diretório 'src'
cd /opt/render/project/src

# Instalar as dependências do projeto usando pip
pip install -r requirements.txt

# Verifica se o arquivo manage.py existe no diretório atual antes de continuar
if [ ! -f "manage.py" ]; then
    echo "Erro: O arquivo manage.py não foi encontrado no diretório /opt/render/project/src."
    echo "Certifique-se de que a estrutura do seu projeto está correta."
    exit 1
fi

# Coletar os arquivos estáticos para o Gunicorn
python manage.py collectstatic --noinput

# Executar as migrações do banco de dados
python manage.py migrate
