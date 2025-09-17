from extensions import db
from datetime import datetime, timedelta
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import enum
from sqlalchemy import Numeric
from sqlalchemy.orm import relationship

# Enum para status de pedidos
class OrderStatus(enum.Enum):
    PENDING = 'Pendente'
    PREPARING = 'Em Preparo'
    SENT = 'Enviado'
    ON_THE_WAY = 'Em Rota de Entrega'
    DELIVERED = 'Entregue'
    CANCELLED = 'Cancelado'
    COMPLETED = 'Concluído'

# Relação N:N para permissões de usuários
user_permissions = db.Table('user_permissions',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permission.id'), primary_key=True)
)

# Modelo de Usuário
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    whatsapp = db.Column(db.String(20), nullable=True)
    
    # Relacionamentos
    subscriptions = db.relationship('Subscription', backref='user', lazy='dynamic')
    orders = db.relationship('Order', backref='user', lazy=True)
    products = db.relationship('Product', backref='user', lazy=True)
    cash_movements = db.relationship('CashMovement', backref='user', lazy=True)
    cash_sessions = db.relationship('CashSession', backref='user', lazy=True)
    customers = db.relationship('Customer', backref='user', lazy=True)
    restaurants = db.relationship('Restaurant', backref='owner', uselist=False, lazy=True)
    neighborhoods = db.relationship('Neighborhood', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_menu_link(self):
        return f"/cardapio/{self.id}"

    def has_active_plan(self):
        active_subscription = self.subscriptions.filter_by(status='active').first()
        if active_subscription and active_subscription.end_date and active_subscription.end_date > datetime.utcnow():
            return True
        return False

# Modelo de Restaurante
class Restaurant(db.Model):
    __tablename__ = 'restaurants'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Este relacionamento foi corrigido para usar backref, que é mais simples
    # para a relação de um-para-um já que o relacionamento já existe
    # na classe de User
    config = db.relationship('RestaurantConfig', backref='restaurant', uselist=False, lazy=True)


# Modelo de Configurações do Restaurante
class RestaurantConfig(db.Model):
    __tablename__ = 'restaurant_configs'
    id = db.Column(db.Integer, primary_key=True)
    # A chave estrangeira CRÍTICA que linka com o Restaurante
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), unique=True, nullable=False)
    
    restaurant_status = db.Column(db.String(20), default='offline')
    description = db.Column(db.Text, default='')
    cover_url = db.Column(db.String(255), nullable=True)
    default_delivery_fee = db.Column(Numeric(10, 2), default=0.0)
    free_delivery_threshold = db.Column(Numeric(10, 2), default=0.0)
    categories = db.Column(db.Text, default='[]')
    email_notifications = db.Column(db.Boolean, default=False)
    sms_notifications = db.Column(db.Boolean, default=False)

    logo_url = db.Column(db.String(255), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    delivery_time_min = db.Column(db.Integer, default=30)
    delivery_time_max = db.Column(db.Integer, default=60)
    pickup_time = db.Column(db.Integer, default=20)
    payment_methods = db.Column(db.Text, default='{}')
    business_hours = db.Column(db.Text, default='{}')
    phone = db.Column(db.String(20), nullable=True)
    pix_key = db.Column(db.String(255), nullable=True)
    manual_status_override = db.Column(db.String(10), default='auto')

class Permission(db.Model):
    __tablename__ = 'permission'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))

# Modelo para Clientes
class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    orders = db.relationship('Order', backref='customer', lazy=True)

# Modelo de Plano de Assinatura
class Plan(db.Model):
    __tablename__ = 'plans'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    price = db.Column(Numeric(10, 2), nullable=False)
    duration_days = db.Column(db.Integer, nullable=False)
    kirvano_checkout_url = db.Column(db.String(255), nullable=True)

    subscriptions = db.relationship('Subscription', backref='plan', lazy=True)
    
# Modelo de Assinatura
class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('plans.id'), nullable=False)
    status = db.Column(db.String(50), default='pending')
    
    kirvano_transaction_id = db.Column(db.String(255), nullable=True, unique=True)
    kirvano_subscription_id = db.Column(db.String(255), nullable=True, unique=True)
    
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=True)
    
    def set_active(self, duration_days):
        self.status = 'active'
        self.end_date = datetime.utcnow() + timedelta(days=duration_days)
    
    def set_canceled(self):
        self.status = 'canceled'
        
# Modelo de Produto
class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(Numeric(10, 2), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    category = db.Column(db.String(50), nullable=True)
    photo_url = db.Column(db.String(255), nullable=True)
    is_delivery = db.Column(db.Boolean, default=True)
    is_balcao = db.Column(db.Boolean, default=True)
    
    order_items = db.relationship('OrderItem', backref='product', lazy=True)

# Modelo de Pedido
class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    client_name = db.Column(db.String(100))
    client_phone = db.Column(db.String(20))
    client_address = db.Column(db.String(200))
    total_price = db.Column(Numeric(10, 2), nullable=False)
    delivery_fee = db.Column(Numeric(10, 2), nullable=False, default=0.0)
    status = db.Column(db.Enum(OrderStatus), default=OrderStatus.PENDING)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    canceled_at = db.Column(db.DateTime, nullable=True)
    
    payment_method = db.Column(db.String(50), nullable=True)
    change_for = db.Column(Numeric(10, 2), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade="all, delete-orphan")
    
    complement_note = db.Column(db.Text, nullable=True)

# Modelo de Item do Pedido
class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_at_order = db.Column(Numeric(10, 2), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    
# Modelo de Movimentação de Caixa
class CashMovement(db.Model):
    __tablename__ = 'cash_movements'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(Numeric(10, 2), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    session_id = db.Column(db.Integer, db.ForeignKey('cash_sessions.id'), nullable=True)
    
# Modelo de Sessão de Caixa
class CashSession(db.Model):
    __tablename__ = 'cash_sessions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    opening_amount = db.Column(Numeric(10, 2), nullable=False)
    closing_amount = db.Column(Numeric(10, 2), nullable=True)
    opened_at = db.Column(db.DateTime, default=datetime.utcnow)
    closed_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    movements = db.relationship('CashMovement', backref='session', lazy=True)

# Modelo de Bairro para Entrega
class Neighborhood(db.Model):
    __tablename__ = 'neighborhoods'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    delivery_fee = db.Column(Numeric(10, 2), nullable=False, default=0.0)
