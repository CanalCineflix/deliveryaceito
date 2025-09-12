import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_login import LoginManager, login_required, current_user
from datetime import datetime, timedelta
# Importe o objeto de configuração
from config import Config

# Importe as extensões e os modelos
from extensions import db, migrate
from models import User, Plan, Subscription, Product, Order, OrderItem, CashMovement, CashSession, OrderStatus, RestaurantConfig, Neighborhood

# Configuração da aplicação
app = Flask(__name__)
app.config.from_object(Config)

# Inicializar as extensões de forma "lazy"
db.init_app(app)
migrate.init_app(app, db)
login_manager = LoginManager()
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
from routes.blocked_routes import blocked_bp # Novo: Importa o blueprint de bloqueio

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
app.register_blueprint(blocked_bp) # Novo: Registra o blueprint de bloqueio

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


def create_sample_data():
    """Cria dados de exemplo para testes"""
    with app.app_context():
        # Cria os planos se não existirem
        planos_data = [
            {'name': 'Freemium', 'description': '15 dias de acesso grátis', 'price': 0.0, 'duration_days': 15},
            {'name': 'Premium', 'description': 'Acesso completo por 30 dias', 'price': 49.90, 'duration_days': 30},
        ]
        for data in planos_data:
            plan = Plan.query.filter_by(name=data['name']).first()
            if not plan:
                new_plan = Plan(**data)
                db.session.add(new_plan)
        db.session.commit()
        
        # Cria o usuário admin se não existir
        admin_user = User.query.filter_by(email='admin@getsolution.com').first()
        if not admin_user:
            admin_user = User(
                name='Admin GetSolution',
                email='admin@getsolution.com',
                phone='(11) 99999-9999',
                restaurant_name='Restaurante Teste'
            )
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()
            
        # Cria produtos de exemplo se não existirem
        if admin_user and not Product.query.filter_by(user_id=admin_user.id).first():
            products_data = [
                {'name': 'Pizza de Calabresa', 'description': 'A melhor pizza de calabresa da cidade', 'price': 45.00, 'category': 'Pizzas'},
                {'name': 'Hambúrguer Clássico', 'description': 'Pão, carne, queijo e salada', 'price': 25.50, 'category': 'Lanches'},
                {'name': 'Coca-Cola 350ml', 'description': 'Refrigerante gelado', 'price': 6.00, 'category': 'Bebidas'},
            ]
            for data in products_data:
                new_product = Product(user_id=admin_user.id, **data)
                db.session.add(new_product)
            db.session.commit()
            
        # Cria as configurações do restaurante se não existirem
        config = RestaurantConfig.query.filter_by(user_id=admin_user.id).first()
        if not config:
            config = RestaurantConfig(
                user_id=admin_user.id,
                business_hours='Segunda a Sábado, 09:00 - 22:00',
                manual_status_override='Aberto',
                pix_key='sua_chave_pix_aqui'
            )
            db.session.add(config)
            db.session.commit()
            
        # Cria bairros de exemplo se não existirem
        neighborhoods_data = [
            {"name": "Centro", "delivery_fee": 5.00},
            {"name": "América", "delivery_fee": 7.50},
            {"name": "Boa Vista", "delivery_fee": 10.00}
        ]
        for data in neighborhoods_data:
            neighborhood = Neighborhood.query.filter_by(name=data['name'], user_id=admin_user.id).first()
            if not neighborhood:
                neighborhood = Neighborhood(
                    user_id=admin_user.id,
                    name=data['name'],
                    delivery_fee=data['delivery_fee']
                )
                db.session.add(neighborhood)
            db.session.commit()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'app': app, 'User': User, 'Plan': Plan, 'Subscription': Subscription}

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_sample_data()
    
    app.run(debug=True, host='0.0.0.0', port=5000)
