import os
import csv
import io
from flask import Blueprint, render_template, request, jsonify, Response
from flask_login import login_required, current_user
from models import db, Order, OrderStatus, CashMovement, OrderItem, Product
from datetime import datetime, timedelta
from sqlalchemy import func, case, extract
from sqlalchemy.orm import joinedload
from collections import defaultdict

reports_bp = Blueprint('reports', __name__, url_prefix='/relatorios', 
template_folder=os.path.join(os.path.dirname(__file__), '../templates/reports'))

def get_date_range():
    """
    Retorna o intervalo de datas do request.
    Ajusta a end_date para incluir o dia inteiro selecionado.
    """
    end_date_str = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    start_date_str = request.args.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    # A end_date vai até 23:59:59 para incluir todos os pedidos do dia
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1, seconds=-1)
    
    return start_date, end_date, start_date_str, end_date_str

# Rota de índice para a seção de relatórios
@reports_bp.route('/')
@login_required
def index():
    """
    Página de índice para a seção de relatórios, servindo como um menu de navegação.
    """
    # Use o caminho 'index.html', pois o Blueprint já sabe que a pasta é 'reports'
    return render_template('reports/index.html') 

@reports_bp.route('/financeiro')
@login_required
def financial():
    start_date, end_date, start_date_str, end_date_str = get_date_range()

    # Consulta unificada para todas as movimentações de caixa no período
    cash_movements = CashMovement.query.filter(
        CashMovement.user_id == current_user.id,
        CashMovement.created_at.between(start_date, end_date)
    ).order_by(CashMovement.created_at.desc()).all()
    
    # Cálculos: entradas e saídas
    sales_entries = sum(float(m.amount) for m in cash_movements if m.type == 'sale')
    expenses_and_refunds = sum(float(m.amount) for m in cash_movements if m.type in ['refund', 'expense'])
    
    all_transactions = cash_movements

    # Labels e valores para o gráfico
    labels = ["Vendas", "Despesas/Reembolsos"]
    values = [sales_entries, expenses_and_refunds]

    chart_data = {
        "labels": labels,
        "values": values
    }

    return render_template(
        'reports/financial.html',
        start_date=start_date_str,
        end_date=end_date_str,
        sales_entries=sales_entries,
        expenses_and_refunds=expenses_and_refunds,
        saldo_final=sales_entries - expenses_and_refunds,
        chart_data=chart_data,
        all_transactions=all_transactions
    )

@reports_bp.route('/vendas')
@login_required
def sales():
    start_date, end_date, start_date_str, end_date_str = get_date_range()

    # Consulta única para todos os pedidos concluídos, com joinedload para evitar N+1 queries
    all_sales = db.session.query(Order).options(joinedload(Order.customer)).filter(
        Order.user_id == current_user.id,
        Order.status == OrderStatus.COMPLETED,
        Order.completed_at.between(start_date, end_date)
    ).order_by(Order.completed_at.desc()).all()
    
    # Agrupar vendas por dia para o gráfico de linha
    sales_by_day = defaultdict(float)
    for sale in all_sales:
        day = sale.completed_at.strftime('%Y-%m-%d')
        sales_by_day[day] += sale.total_price

    chart_labels = sorted(sales_by_day.keys())
    chart_values = [sales_by_day[day] for day in chart_labels]
    
    # Calcular a receita total para o template
    total_revenue = sum(sale.total_price for sale in all_sales)

    if len(all_sales) > 0:
        avg_ticket = total_revenue / len(all_sales)
    else:
        avg_ticket = 0.0

    return render_template(
        'reports/sales.html',
        start_date=start_date_str,
        end_date=end_date_str,
        all_sales=all_sales,
        chart_labels=chart_labels,
        chart_values=chart_values,
        total_revenue=total_revenue,
        avg_ticket=avg_ticket,
        total_orders=len(all_sales)
    )

@reports_bp.route('/vendas/export-csv')
@login_required
def export_sales_csv():
    start_date, end_date, _, _ = get_date_range()
    
    # Consulta que busca todas as vendas no período, com joinedload para acessar o cliente
    all_sales = db.session.query(Order).options(joinedload(Order.customer)).filter(
        Order.user_id == current_user.id,
        Order.status == OrderStatus.COMPLETED,
        Order.completed_at.between(start_date, end_date)
    ).order_by(Order.completed_at.desc()).all()

    # Cria um buffer de memória para o arquivo CSV
    si = io.StringIO()
    cw = csv.writer(si)

    # Escreve o cabeçalho
    header = ['ID do Pedido', 'Data', 'Cliente', 'Total', 'Método de Pagamento']
    cw.writerow(header)

    # Escreve os dados
    for sale in all_sales:
        # Acesso seguro ao nome do cliente
        customer_name = sale.customer.name if sale.customer else 'Não Informado'
        row = [
            f'#{sale.id}',
            sale.completed_at.strftime('%d/%m/%Y %H:%M'),
            customer_name,
            f'{sale.total_price:.2f}', # Removido 'R$' para facilitar o uso em planilhas
            sale.payment_method
        ]
        cw.writerow(row)

    # Retorna o arquivo como uma resposta de download
    return Response(
        si.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=relatorio_vendas.csv'}
    )

@reports_bp.route('/produtos')
@login_required
def products():
    start_date, end_date, start_date_str, end_date_str = get_date_range()

    # Consulta os produtos mais vendidos dentro do intervalo de tempo
    top_products = db.session.query(
        Product.name,
        func.sum(OrderItem.quantity).label('total_quantity'),
        func.sum(OrderItem.quantity * OrderItem.price_at_order).label('total_revenue')
    ).join(
        OrderItem, Product.id == OrderItem.product_id
    ).join(
        Order, OrderItem.order_id == Order.id
    ).filter(
        Order.user_id == current_user.id,
        Order.status == OrderStatus.COMPLETED,
        Order.completed_at.between(start_date, end_date)
    ).group_by(
        Product.id, Product.name
    ).order_by(
        func.sum(OrderItem.quantity).desc()
    ).limit(10).all()
    
    chart_labels = [p.name for p in top_products]
    chart_values = [p.total_quantity for p in top_products]
    
    return render_template(
        'reports/products.html',
        start_date=start_date_str,
        end_date=end_date_str,
        top_products=top_products,
        chart_labels=chart_labels,
        chart_values=chart_values
    )

@reports_bp.route('/produtos/export-csv')
@login_required
def export_products_csv():
    start_date, end_date, _, _ = get_date_range()
    
    top_products = db.session.query(
        Product.name,
        func.sum(OrderItem.quantity).label('total_quantity'),
        func.sum(OrderItem.quantity * OrderItem.price_at_order).label('total_revenue')
    ).join(
        OrderItem, Product.id == OrderItem.product_id
    ).join(
        Order, OrderItem.order_id == Order.id
    ).filter(
        Order.user_id == current_user.id,
        Order.status == OrderStatus.COMPLETED,
        Order.completed_at.between(start_date, end_date)
    ).group_by(
        Product.id, Product.name
    ).order_by(
        func.sum(OrderItem.quantity).desc()
    ).all()

    si = io.StringIO()
    cw = csv.writer(si)

    cw.writerow(['Nome do Produto', 'Quantidade Vendida', 'Receita Total'])
    
    for p in top_products:
        cw.writerow([p.name, p.total_quantity, f'R$ {p.total_revenue:.2f}'])

    return Response(
        si.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=relatorio_produtos.csv'}
    )