# Importa módulos necessários
import os
import subprocess  # Importa o módulo subprocess
from dotenv import load_dotenv
from flask import Flask
from extensions import db, migrate
from models import User, Plan, Subscription, Product, Order, OrderItem, CashMovement, CashSession, OrderStatus, RestaurantConfig, Neighborhood
from config import Config

# Carrega as variáveis de ambiente
load_dotenv()

# Inicializa o aplicativo Flask
app = Flask(__name__)
app.config.from_object(Config)

# Inicializa as extensões
db.init_app(app)
migrate.init_app(app, db)

# Adiciona todos os modelos ao contexto da aplicação
with app.app_context():
    pass

if __name__ == '__main__':
    print("Iniciando o processo de migração do banco de dados...")
    
    # Executa as migrações em duas etapas para garantir que o Alembic
    # crie e aplique a migração corretamente no ambiente do Render.

    # 1. Limpa o histórico de migrações
    print("Resetando o histórico de migrações...")
    subprocess.run(["flask", "db", "stamp", "head"], check=True)
    
    # 2. Cria uma nova migração 'autogenerate' baseada nos modelos atuais.
    # Isso garante que todas as colunas e tabelas necessárias existam no banco de dados.
    print("Criando nova migração...")
    subprocess.run(["flask", "db", "migrate", "-m", "Recriação da estrutura de dados"], check=True)
    
    # 3. Aplica as migrações pendentes, incluindo a que acabamos de criar.
    print("Aplicando as migrações...")
    subprocess.run(["flask", "db", "upgrade"], check=True)
    
    print("Processo de migração concluído.")
