# 1. Define a variável de ambiente DATABASE_URL explicitamente
# Isso contorna o problema de o Flask não a encontrar automaticamente, garantindo
# que a variável exista antes de qualquer importação que a utilize.
import os
import subprocess  # Importa o módulo subprocess
os.environ['DATABASE_URL'] = "postgresql://deliveryaceito_db_user:AGta17Rfo8XZxvewpmza0qYIP4KNSk8p@dpg-d307bg15pdvs73f70i20-a/deliveryaceito_db"

from dotenv import load_dotenv
from flask import Flask
from extensions import db, migrate
from models import User, Plan, Subscription, Product, Order, OrderItem, CashMovement, CashSession, OrderStatus, RestaurantConfig, Neighborhood
from config import Config

# 2. Carrega as variáveis de ambiente do arquivo .env
load_dotenv()


# 3. Inicializa o aplicativo Flask
app = Flask(__name__)
app.config.from_object(Config)

# 4. Inicializa as extensões
db.init_app(app)
migrate.init_app(app, db)

# 5. Adiciona todos os modelos ao contexto da aplicação
with app.app_context():
    pass

if __name__ == '__main__':
    # 6. Executa os comandos de migração usando o subprocess.run()
    # Isso garante que a aplicação e as variáveis de ambiente estejam prontas
    # antes de chamar o Flask-Migrate.
    print("Iniciando a migração do banco de dados...")
    
    # Para criar uma migração, use subprocess.run com a mensagem de commit como um item da lista.
    # Exemplo: subprocess.run(["flask", "db", "migrate", "-m", "Adiciona coluna de email"])
    
    # Para aplicar a migração, use:
    # subprocess.run(["flask", "db", "upgrade"])
    
    # Para sua tarefa atual, o comando é:
    subprocess.run(["flask", "db", "migrate", "-m", "Aumenta o tamanho da coluna password_hash"])

    print("Processo de migração concluído.")
