import os
from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import current_user
from datetime import datetime

# Carrega as variáveis de ambiente (Render já injeta em produção)
if not os.environ.get('RENDER'):
    load_dotenv()
    load_dotenv('.env.local', override=True)

# Configuração
from config import Config
from extensions import db, migrate, login_manager
from models import (
    User, Plan, Subscription, Product, Order, OrderItem,
    CashMovement, CashSession, OrderStatus, RestaurantConfig, Neighborhood
)

# Inicializa app
app = Flask(__name__)
app.config.from_object(Config)

# Inicializa extensões
db.init_app(app)
migrate.init_app(app, db)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Você precisa fazer login para acessar esta página.'
login_manager.login_message_category = 'info'

# User loader
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# === Blueprints ===
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
from rotas.webhooks_bp import webhooks_bp # Importação correta

app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
app.register_blueprint(pedidos_bp)
app.register_blueprint(caixa_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(perfil_bp)
app.register_blueprint(planos_bp, url_prefix='/planos')
app.register_blueprint(cardapio_bp)
app.register_blueprint(produtos_bp)
app.register_blueprint(payments_bp, url_prefix='/payments')  # checkout
app.register_blueprint(webhooks_bp, url_prefix='/webhooks')   # webhooks externos (Registro corrigido)
app.register_blueprint(blocked_bp)

# === Contexto Global ===
@app.context_processor
def inject_globals():
    return dict(current_user=current_user, now=datetime.utcnow())

# === Rotas principais ===
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return render_template('index.html')

# Middleware para checagem de plano
@app.before_request
def check_plan_access():
    protected_routes = ['dashboard', 'pedidos', 'caixa', 'reports', 'perfil', 'produtos']
    if request.endpoint and any(r in request.endpoint for r in ['static', 'auth', 'cardapio', 'planos', 'payments', 'webhooks', 'blocked']):
        return
    if request.endpoint and any(r in request.endpoint for r in protected_routes):
        if current_user.is_authenticated and not current_user.has_active_plan():
            flash('Seu plano expirou. Por favor, assine um plano Premium para continuar.', 'warning')
            return redirect(url_for('blocked.blocked'))

# Shell
@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'app': app, 'User': User, 'Plan': Plan, 'Subscription': Subscription}

# Run
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
