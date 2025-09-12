import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_login import current_user
from datetime import datetime, timedelta
# Importe o objeto de configuração
from config import Config

# Importe as extensões e os modelos
from extensions import db, migrate, login_manager
from models import User, Plan, Subscription, Product, Order, OrderItem, CashMovement, CashSession, OrderStatus, RestaurantConfig, Neighborhood

# Configuração da aplicação
app = Flask(__name__)
app.config.from_object(Config)

# Inicializar as extensões de forma "lazy" ou diretamente após o app
db.init_app(app)
migrate.init_app(app, db)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Você precisa fazer login para acessar esta página.'
login_manager.login_message_category = 'info'

# Função para carregar o usuário
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Registrar blueprints DEPOIS que o app e o db estão inicializados
from routes.auth_routes import auth_bp
from routes.dashboard_routes import dashboard_bp
from routes.pedidos_routes import pedidos_bp
from routes.caixa_routes import caixa_bp
from routes.reports_routes import reports_bp
from routes.perfil_routes import perfil_bp
from routes.planos_routes import planos_bp
from routes.cardapio_routes import cardapio_bp
from routes.produtos_routes import produtos_bp
from routes.payments_routes import payments_bp
from routes.blocked_routes import blocked_bp

app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
app.register_blueprint(pedidos_bp)
app.register_blueprint(caixa_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(perfil_bp)
app.register_blueprint(planos_bp, url_prefix='/planos')
app.register_blueprint(cardapio_bp)
app.register_blueprint(produtos_bp)
app.register_blueprint(payments_bp, url_prefix='/webhooks/payments')
app.register_blueprint(blocked_bp)

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return render_template('index.html')

@app.context_processor
def inject_user():
    return dict(current_user=current_user)

@app.before_request
def check_plan_access():
    """Middleware para verificar acesso baseado no plano, usando a nova lógica."""
    protected_routes = ['dashboard', 'pedidos', 'caixa', 'reports', 'perfil', 'produtos']
    
    # Exclui rotas públicas, estáticas e de autenticação/planos/pagamentos
    if request.endpoint and any(route in request.endpoint for route in ['static', 'auth', 'cardapio', 'planos', 'payments', 'blocked']):
        return
        
    if request.endpoint and any(route in request.endpoint for route in protected_routes):
        if current_user.is_authenticated and not current_user.has_active_plan():
            flash('Seu plano expirou. Por favor, assine um plano Premium para continuar.', 'warning')
            return redirect(url_for('blocked.blocked'))


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'app': app, 'User': User, 'Plan': Plan, 'Subscription': Subscription}

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
