from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from models import db
from models import Product, Order, OrderItem, OrderStatus
from sqlalchemy import func, extract
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__, template_folder='../templates/dashboard')

@dashboard_bp.route('/')
@login_required
def index():
    user_id = current_user.id
    
    # 1. Métricas do Dashboard
    today = datetime.now().date()
    start_of_month = today.replace(day=1)
    
    # Total de pedidos hoje
    total_orders_today = Order.query.filter(
        Order.user_id == user_id,
        func.date(Order.created_at) == today
    ).count()
    
    # Receita total hoje
    revenue_today = db.session.query(func.sum(Order.total_price)).filter(
        Order.user_id == user_id,
        func.date(Order.created_at) == today,
        Order.status == OrderStatus.COMPLETED
    ).scalar() or 0
    
    # Receita total no mês
    revenue_month = db.session.query(func.sum(Order.total_price)).filter(
        Order.user_id == user_id,
        extract('month', Order.created_at) == today.month,
        extract('year', Order.created_at) == today.year,
        Order.status == OrderStatus.COMPLETED
    ).scalar() or 0

    # Total de pedidos no mês
    total_orders_month = Order.query.filter(
        Order.user_id == user_id,
        extract('month', Order.created_at) == today.month,
        extract('year', Order.created_at) == today.year
    ).count()
    
    # Ticket Médio do Mês
    if total_orders_month > 0:
        avg_ticket = revenue_month / total_orders_month
    else:
        avg_ticket = 0
    
    # 2. Pedidos recentes
    recent_orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).limit(10).all()
    
    # 3. Produtos mais vendidos
    top_products = db.session.query(
        Product.name,
        func.sum(OrderItem.quantity).label('total_sold')
    ).join(OrderItem, Product.id == OrderItem.product_id).filter(
        Product.user_id == user_id
    ).join(Order, Order.id == OrderItem.order_id).filter(
        Order.status == OrderStatus.COMPLETED
    ).group_by(Product.name).order_by(func.sum(OrderItem.quantity).desc()).limit(5).all()

    # 4. Tendência de Vendas (últimos 7 dias)
    sales_trend = []
    for i in range(7):
        day = today - timedelta(days=6 - i)
        daily_revenue = db.session.query(func.sum(Order.total_price)).filter(
            Order.user_id == user_id,
            func.date(Order.created_at) == day,
            Order.status == OrderStatus.COMPLETED
        ).scalar() or 0
        sales_trend.append({'date': day.strftime('%d/%m'), 'revenue': float(daily_revenue)})
        
    context = {
        'total_orders_today': total_orders_today,
        'revenue_today': revenue_today,
        'daily_revenue': revenue_today,
        'total_orders_month': total_orders_month,
        'revenue_month': revenue_month,
        'avg_ticket': avg_ticket,
        'recent_orders': recent_orders,
        'top_products': top_products,
        'sales_trend': sales_trend,
    }
    
    return render_template('dashboard/index.html', **context)