import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Order, OrderItem, Product, CashMovement, OrderStatus
from datetime import datetime
from sqlalchemy import func
import json
from sqlalchemy.orm import joinedload
from decimal import Decimal 

pedidos_bp = Blueprint('pedidos', __name__, url_prefix='/pedidos', 
template_folder=os.path.join(os.path.dirname(__file__), '../templates/pedidos'))

@pedidos_bp.route('/')
@login_required
def index():
    """
    Rota principal para exibir os pedidos, com a opção de filtrar por status.
    """
    status = request.args.get('status', 'PENDING').upper()
    
    # Apenas os status PENDING, PREPARING e SENT são exibidos nesta tela
    valid_statuses = [OrderStatus.PENDING, OrderStatus.PREPARING, OrderStatus.SENT]
    
    if status not in [s.name for s in valid_statuses]:
        flash('Status de pedido inválido.', 'danger')
        return redirect(url_for('pedidos.index', status='PENDING'))
        
    orders = Order.query.options(
        joinedload(Order.items).joinedload(OrderItem.product)
    ).filter(
        Order.user_id == current_user.id,
        Order.status == OrderStatus[status]
    ).order_by(Order.created_at.desc()).all()

    return render_template('pedidos/index.html', orders=orders, OrderStatus=OrderStatus, status=status)

@pedidos_bp.route('/concluidos', methods=['GET'])
@login_required
def concluidos():
    # ... (código inalterado)
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    query = Order.query.filter(
        Order.user_id == current_user.id,
        Order.status == OrderStatus.COMPLETED
    )
    
    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        query = query.filter(func.date(Order.completed_at) >= start_date)
    
    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        query = query.filter(func.date(Order.completed_at) <= end_date)
    
    completed_orders = query.order_by(Order.completed_at.desc()).all()
    
    grouped_by_date = {}
    for order in completed_orders:
        if order.completed_at:
            date_key = order.completed_at.strftime('%d/%m/%Y')
            if date_key not in grouped_by_date:
                grouped_by_date[date_key] = []
            grouped_by_date[date_key].append(order)
            
    return render_template('pedidos/concluded.html', 
        grouped_orders=grouped_by_date,
        start_date=start_date_str,
        end_date=end_date_str)

@pedidos_bp.route('/cancelados', methods=['GET'])
@login_required
def cancelados():
    # ... (código inalterado)
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    query = Order.query.filter(
        Order.user_id == current_user.id,
        Order.status == OrderStatus.CANCELLED
    )
    
    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        query = query.filter(func.date(Order.canceled_at) >= start_date)
    
    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        query = query.filter(func.date(Order.canceled_at) <= end_date)

    cancelled_orders = query.order_by(Order.canceled_at.desc()).all()
    
    grouped_by_date = {}
    for order in cancelled_orders:
        if order.canceled_at:
            date_key = order.canceled_at.strftime('%d/%m/%Y')
            if date_key not in grouped_by_date:
                grouped_by_date[date_key] = []
            grouped_by_date[date_key].append(order)
            
    return render_template(
        'pedidos/cancelados.html', 
        grouped_orders=grouped_by_date,
        start_date=start_date_str,
        end_date=end_date_str
    )

@pedidos_bp.route('/<int:order_id>/cancelar', methods=['POST'])
@login_required
def cancel_order(order_id):
    # ... (código inalterado)
    order = Order.query.filter(
        Order.id == order_id,
        Order.user_id == current_user.id
    ).first_or_404()
    
    cancel_reason = request.form.get('cancel_reason', 'Motivo não especificado.')

    order.status = OrderStatus.CANCELLED
    order.canceled_at = datetime.utcnow()
    order.cancel_reason = cancel_reason
    db.session.commit()

    flash(f'Pedido #{order.id} cancelado com sucesso.', 'success')
    return redirect(url_for('pedidos.cancelados'))

@pedidos_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def new_order():
    if request.method == 'POST':
        order_data = request.get_json()

        if not order_data:
            return jsonify({'success': False, 'message': 'Dados de pedido ausentes.'}), 400

        customer_name = order_data.get('customer_name')
        customer_phone = order_data.get('customer_phone')
        customer_address = order_data.get('client_address') # Verifique se o frontend usa client_address
        customer_notes = order_data.get('complement_note')  # Verifique se o frontend usa complement_note ou customer_notes
        payment_method = order_data.get('payment_method')
        table_number = order_data.get('table_number')
        
        # 🚨 CORREÇÃO PRINCIPAL AQUI: Usa 'order_items' para capturar a lista de itens
        items_data = order_data.get('order_items', []) 

        try:
            # Criação inicial do objeto Order
            order = Order(
                user_id=current_user.id,
                client_name=customer_name,
                client_phone=customer_phone,
                client_address=customer_address,
                payment_method=payment_method,
                total_price=0.0, 
                table_number=table_number,
                notes=customer_notes
            )
            
            db.session.add(order)
            db.session.flush() 
            
            total_price = Decimal(0)
            
            # Adicione a taxa de entrega ao preço inicial, se for o caso.
            # No seu caso, o total de R$ 10.00 é a taxa. Se você não está calculando a taxa na rota do Cardápio,
            # ela deve ser adicionada aqui.
            # total_price = total_price + Decimal('10.00') # Exemplo se 10.00 for a taxa fixa
            
            for item_data in items_data:
                
                # Garante que ID e Quantidade são inteiros (int)
                try:
                    product_id = int(item_data.get('id'))
                    quantity = int(item_data.get('quantity'))
                except (TypeError, ValueError):
                    continue
                    
                # Usa 'note' para observação, conforme o log
                observation = item_data.get('note', '') 
                
                if quantity <= 0:
                    continue
                
                product = Product.query.get(product_id)
                
                if product:
                    item = OrderItem(
                        order_id=order.id,
                        product_id=product.id,
                        quantity=quantity,
                        price_at_order=product.price,
                        notes=observation
                    )
                    db.session.add(item)
                    total_price += Decimal(product.price) * Decimal(quantity)
                else:
                    print(f"Produto não encontrado para ID: {product_id}. Item ignorado.") 
            
            # Se o valor total de R$ 10.00 deve ser adicionado *após* a soma dos itens:
            # Assumindo que R$ 10.00 é a taxa de entrega:
            delivery_fee = Decimal('10.00') # Você deve buscar esse valor do DB ou do JSON
            order.total_price = total_price + delivery_fee
            
            db.session.commit()
            
            flash('Pedido criado com sucesso!', 'success')
            return jsonify({'success': True, 'redirect_url': url_for('pedidos.index')}), 200
            
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao criar pedido: {e}") 
            flash(f'Ocorreu um erro ao criar o pedido: {e}', 'danger')
            return jsonify({'success': False, 'message': str(e)}), 500

    products = Product.query.filter(
        Product.user_id == current_user.id,
        Product.is_active == True
    ).all()
    
    return render_template('pedidos/new.html', products=products)


@pedidos_bp.route('/<int:order_id>/status/next', methods=['POST'])
@login_required
def next_status(order_id):
    # ... (código inalterado)
    order = Order.query.filter(
        Order.id == order_id,
        Order.user_id == current_user.id
    ).first_or_404()

    status_sequence = {
        OrderStatus.PENDING: OrderStatus.PREPARING,
        OrderStatus.PREPARING: OrderStatus.SENT,
        OrderStatus.SENT: OrderStatus.COMPLETED
    }

    if order.status in status_sequence:
        next_status = status_sequence[order.status]
        order.status = next_status
        
        if next_status == OrderStatus.COMPLETED:
            order.completed_at = datetime.utcnow()
            cash_movement = CashMovement(
                user_id=current_user.id,
                type='sale',
                description=f'Venda - Pedido #{order.id}',
                amount=order.total_price,
                order_id=order.id
            )
            db.session.add(cash_movement)
        
        db.session.commit()
        flash(f'Status do Pedido #{order.id} atualizado para {next_status.name.replace("_", " ").title()}', 'success')
    else:
        flash(f'O status do Pedido #{order.id} não pode ser avançado.', 'danger')

    return redirect(url_for('pedidos.index', status=order.status.name))

@pedidos_bp.route('/<int:order_id>')
@login_required
def view_order(order_id):
    order = Order.query.options(
        joinedload(Order.items).joinedload(OrderItem.product)
    ).filter(
        Order.id == order_id,
        Order.user_id == current_user.id
    ).first_or_404()
    
    return render_template('pedidos/view.html', order=order)

@pedidos_bp.route('/<int:order_id>/imprimir')
@login_required
def print_comanda(order_id):
    order = Order.query.options(
        joinedload(Order.user), 
        joinedload(Order.items).joinedload(OrderItem.product)
    ).filter(
        Order.id == order_id,
        Order.user_id == current_user.id
    ).first_or_404()
    
    # 🚨 ADICIONE ESTA LÓGICA ANTES DE RENDERIZAR O TEMPLATE:
    troco_devolver = 0
    # Verifica se o pagamento é em dinheiro E se o cliente deu um valor para troco
    if order.payment_method == 'Dinheiro' and order.change_for:
        # Calcula o troco: (Valor dado - Preço Total)
        # Se o troco for positivo, usa-o. Se for zero ou negativo (erro), usa 0.
        troco_calculado = order.change_for - order.total_price
        if troco_calculado > 0:
            troco_devolver = troco_calculado
            
    # Passa a variável extra para o template
    return render_template('pedidos/print_comanda.html', order=order, troco_a_devolver=troco_devolver)
