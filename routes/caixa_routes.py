# Este módulo define as rotas relacionadas ao controle do caixa.
#
# Importa módulos e classes necessários
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, CashSession, CashMovement, Order, Product, OrderItem, OrderStatus, Customer
from datetime import datetime, timedelta
from sqlalchemy import func, extract
from sqlalchemy import case
from collections import defaultdict
from sqlalchemy.orm import joinedload


# Define o Blueprint para as rotas do caixa
caixa_bp = Blueprint('caixa', __name__, url_prefix='/caixa')

@caixa_bp.route('/')
@login_required
def index():
    """
    Rota principal para exibir o status do caixa, movimentos diários e a lista de produtos
    para o "Novo Pedido Manual" quando o caixa estiver aberto.
    """
    # Verificar se há sessão ativa
    active_session = CashSession.query.filter(
        CashSession.user_id == current_user.id,
        CashSession.is_active == True
    ).first()
    
    # Movimentações do dia
    today = datetime.now().date()
    movements = CashMovement.query.filter(
        CashMovement.user_id == current_user.id,
        func.date(CashMovement.created_at) == today
    ).order_by(CashMovement.created_at.desc()).all()
    
  total_sales = sum(m.amount for m in movements if m.type == 'sale')

# Otimizado: Uso de Gerador de Expressão (mantendo abs() para garantir que os gastos sejam somados como positivos)
total_expenses = sum(abs(m.amount) for m in movements if m.type in ['expense', 'withdrawal'])

# CORRIGIDO E OTIMIZADO: Remoção do colchete ] e uso do Gerador de Expressão
total_deposits = sum(m.amount for m in movements if m.type == 'deposit')

    current_balance = 0.0
    if active_session:
        opening_amount = active_session.opening_amount
        balance_change = db.session.query(func.sum(CashMovement.amount)).filter(
            CashMovement.session_id == active_session.id,
            CashMovement.type != 'opening'
        ).scalar() or 0.0
        
        # CORREÇÃO: Ocorre TypeError ao somar Decimal (opening_amount) e float (balance_change=0.0).
        # Convertemos explicitamente opening_amount (Decimal) e balance_change (Decimal ou float)
        # para float para garantir o tipo homogêneo na soma, resolvendo o erro.
        current_balance = float(opening_amount) + float(balance_change)
    
    products = Product.query.filter(
        Product.user_id == current_user.id,
        Product.is_active == True,
        Product.is_balcao == True
    ).all()
    
    # Consulta de pedidos de balcão (sem cliente associado)
    new_counter_orders = db.session.query(Order).options(joinedload(Order.items)).filter(
        Order.user_id == current_user.id,
        Order.status == OrderStatus.COMPLETED,
        func.date(Order.created_at) == today,
        Order.customer_id.is_(None)
    ).order_by(Order.created_at.desc()).all()
    
    return render_template('caixa/index.html',
                            active_session=active_session,
                            movements=movements,
                            total_sales=total_sales,
                            total_expenses=total_expenses,
                            total_deposits=total_deposits,
                            current_balance=current_balance,
                            products=products,
                            new_counter_orders=new_counter_orders)

@caixa_bp.route('/abrir', methods=['POST'])
@login_required
def open_cash():
    active_session = CashSession.query.filter(
        CashSession.user_id == current_user.id,
        CashSession.is_active == True
    ).first()
    
    if active_session:
        flash('Já existe uma sessão de caixa ativa.', 'warning')
        return redirect(url_for('caixa.index'))
    
    try:
        opening_amount = float(request.form.get('opening_amount', 0).replace(',', '.'))
    except (ValueError, TypeError):
        flash('Valor de abertura inválido.', 'danger')
        return redirect(url_for('caixa.index'))

    try:
        session = CashSession(
            user_id=current_user.id,
            opening_amount=opening_amount
        )
        db.session.add(session)
        db.session.flush()

        movement = CashMovement(
            user_id=current_user.id,
            session_id=session.id,
            type='opening',
            description='Abertura de caixa',
            amount=opening_amount
        )
        db.session.add(movement)
        
        db.session.commit()
        
        flash('Caixa aberto com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao abrir o caixa: {str(e)}', 'danger')
    
    return redirect(url_for('caixa.index'))

@caixa_bp.route('/fechar', methods=['POST'])
@login_required
def close_cash():
    active_session = CashSession.query.filter(
        CashSession.user_id == current_user.id,
        CashSession.is_active == True
    ).first()
    
    if not active_session:
        flash('Não há sessão de caixa ativa para fechar.', 'warning')
        return redirect(url_for('caixa.index'))
    
    try:
        closing_amount = float(request.form.get('closing_amount', 0).replace(',', '.'))
    except (ValueError, TypeError):
        flash('Valor de fechamento inválido.', 'danger')
        return redirect(url_for('caixa.index'))
    
    try:
        active_session.closing_amount = closing_amount
        active_session.closed_at = datetime.utcnow()
        active_session.is_active = False
        
        movement = CashMovement(
            user_id=current_user.id,
            session_id=active_session.id,
            type='closing',
            description='Fechamento de caixa',
            amount=closing_amount
        )
        db.session.add(movement)
        
        db.session.commit()
        
        flash('Caixa fechado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao fechar o caixa: {str(e)}', 'danger')

    return redirect(url_for('caixa.index'))

@caixa_bp.route('/movimento', methods=['POST'])
@login_required
def add_movement():
    movement_type = request.form.get('type')
    description = request.form.get('description')
    amount = request.form.get('amount')
    
    if not all([movement_type, description, amount]):
        flash('Todos os campos são obrigatórios.', 'danger')
        return redirect(url_for('caixa.index'))

    try:
        amount = float(amount.replace(',', '.'))
    except (ValueError, TypeError):
        flash('Valor inválido.', 'danger')
        return redirect(url_for('caixa.index'))

    active_session = CashSession.query.filter(
        CashSession.user_id == current_user.id,
        CashSession.is_active == True
    ).first()
    
    if not active_session:
        flash('Caixa não está aberto. Não é possível registrar movimentações.', 'danger')
        return redirect(url_for('caixa.index'))

    if movement_type not in ['expense', 'deposit', 'withdrawal']:
        flash('Tipo de movimentação inválido.', 'danger')
        return redirect(url_for('caixa.index'))

    if movement_type in ['expense', 'withdrawal']:
        amount = -abs(amount)
    
    try:
        movement = CashMovement(
            user_id=current_user.id,
            session_id=active_session.id,
            type=movement_type,
            description=description,
            amount=amount
        )
        
        db.session.add(movement)
        db.session.commit()
        
        flash('Movimentação registrada com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao registrar movimentação: {str(e)}', 'danger')

    return redirect(url_for('caixa.index'))

@caixa_bp.route('/history')
@login_required
def history():
    """
    Rota para exibir o histórico de todas as sessões de caixa e suas movimentações.
    Permite filtrar por um intervalo de datas.
    """
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    query = CashMovement.query.filter_by(user_id=current_user.id)

    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            query = query.filter(CashMovement.created_at >= start_date, CashMovement.created_at <= end_date + timedelta(days=1))
        except ValueError:
            flash('Formato de data inválido. Use AAAA-MM-DD.', 'danger')
            return redirect(url_for('caixa.history'))
    else:
        today = datetime.now()
        query = query.filter(
            extract('year', CashMovement.created_at) == today.year,
            extract('month', CashMovement.created_at) == today.month
        )

    all_movements = query.order_by(CashMovement.created_at.desc()).all()
    
    movements_by_date = defaultdict(list)
    for movement in all_movements:
        date = movement.created_at.date()
        movements_by_date[date].append(movement)

    return render_template(
        'caixa/history.html',
        movements_by_date=movements_by_date,
        start_date=start_date_str,
        end_date=end_date_str
    )
    
@caixa_bp.route('/finalize_counter_order', methods=['POST'])
@login_required
def finalize_counter_order():
    order_data = request.get_json()

    if not order_data:
        return jsonify({'success': False, 'message': 'Dados de pedido ausentes.'}), 400

    active_session = CashSession.query.filter(
        CashSession.user_id == current_user.id,
        CashSession.is_active == True
    ).first()
    
    if not active_session:
        return jsonify({'success': False, 'message': 'Caixa não está aberto. Não é possível registrar vendas.'}), 400

    payment_method = order_data.get('payment_method')
    change_for_str = order_data.get('change_for')
    change_for = float(change_for_str) if change_for_str else None
    notes = order_data.get('notes', '')
    items_data = order_data.get('items', [])
    
    if not items_data:
        return jsonify({'success': False, 'message': 'O pedido deve conter itens.'}), 400
            
    try:
        order = Order(
            user_id=current_user.id,
            payment_method=payment_method,
            change_for=change_for,
            total_price=0.0,
            status=OrderStatus.COMPLETED,
            notes=notes
        )

        db.session.add(order)
        db.session.flush()

        total_price = 0
        order_items_to_print = []

        for item_data in items_data:
            product_id = item_data.get('product_id') 
            quantity = item_data.get('quantity')
            item_notes = item_data.get('notes', '') 
            
            if not product_id or not quantity or quantity <= 0:
                continue
            
            product = Product.query.get(product_id)
            
            if product:
                item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=quantity,
                    price_at_order=product.price,
                    notes=item_notes
                )
                db.session.add(item)
                total_price += product.price * quantity

                order_items_to_print.append({
                    'name': product.name,
                    'quantity': quantity,
                    'price': product.price,
                    'total': product.price * quantity,
                    'notes': item_notes
                })

        order.total_price = total_price
        
        cash_movement = CashMovement(
            user_id=current_user.id,
            session_id=active_session.id,
            type='sale',
            description=f'Venda de Balcão - Pedido #{order.id}',
            amount=order.total_price,
            order_id=order.id
        )
        db.session.add(cash_movement)
        db.session.commit()
        
        receipt_html = render_template(
            'caixa/receipt.html',
            order_id=order.id,
            timestamp=datetime.now().strftime('%d/%m/%Y %H:%M'),
            items=order_items_to_print,
            total_price=order.total_price,
            payment_method=payment_method,
            change_for=change_for,
            notes=notes
        )

        flash('Venda de balcão registrada com sucesso!', 'success')
        return jsonify({
            'success': True,
            'message': 'Venda de balcão registrada com sucesso!',
            'order_id': order.id,
            'receipt_html': receipt_html,  
            'redirect_url': url_for('caixa.index')
        }), 200
            
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao processar o pedido: {e}")
        return jsonify({'success': False, 'message': 'Ocorreu um erro inesperado.'}), 500

@caixa_bp.route('/buscar_produtos')
@login_required
def search_products():
    """
    Busca produtos por nome para a funcionalidade de "Novo Pedido de Balcão".
    """
    query = request.args.get('q', '').strip().lower()
    
    if not query:
        return jsonify([])

    products = Product.query.filter(
        Product.user_id == current_user.id,
        Product.is_active == True,
        Product.is_balcao == True,
        func.lower(Product.name).like(f'%{query}%')
    ).order_by(
        case(
            (func.lower(Product.name).startswith(query), 0),
            else_=1
        ),
        Product.name
    ).limit(10).all()

    results = [
        {
            'id': product.id,
            'name': product.name,
            'price': float(product.price)
        } for product in products
    ]
    
    return jsonify(results)

@caixa_bp.route('/editar_pedido/<int:order_id>', methods=['GET', 'POST'])
@login_required
def editar_pedido(order_id):
    """
    Rota para editar um pedido de balcão.
    No GET, retorna dados para o modal. No POST, salva as alterações.
    """
    order = db.session.query(Order).options(joinedload(Order.items).joinedload(OrderItem.product)).filter(
        Order.id == order_id, 
        Order.user_id == current_user.id
    ).first_or_404()

    if request.method == 'POST':
        try:
            order_data = request.get_json()
            if not order_data:
                return jsonify({'success': False, 'message': 'Dados de pedido ausentes.'}), 400

            new_notes = order_data.get('notes', '')
            items_data = order_data.get('items', [])
            
            # Deleta os itens antigos
            OrderItem.query.filter_by(order_id=order.id).delete()

            new_total_price = 0
            for item_data in items_data:
                product_id = item_data.get('product_id')
                quantity = item_data.get('quantity')
                item_notes = item_data.get('notes', '')

                if not product_id or quantity <= 0:
                    continue
                
                product = Product.query.get(product_id)
                if product:
                    new_item = OrderItem(
                        order_id=order.id,
                        product_id=product.id,
                        quantity=quantity,
                        price_at_order=product.price,
                        notes=item_notes
                    )
                    db.session.add(new_item)
                    new_total_price += product.price * quantity

            # Atualiza o pedido e o movimento de caixa
            order.notes = new_notes
            order.total_price = new_total_price
            
            cash_movement = CashMovement.query.filter_by(order_id=order.id).first()
            if cash_movement:
                cash_movement.amount = new_total_price
            else:
                active_session = CashSession.query.filter(
                    CashSession.user_id == current_user.id,
                    CashSession.is_active == True
                ).first()
                if active_session:
                    new_movement = CashMovement(
                        user_id=current_user.id,
                        session_id=active_session.id,
                        type='sale',
                        description=f'Venda de Balcão (Editado) - Pedido #{order.id}',
                        amount=new_total_price,
                        order_id=order.id
                    )
                    db.session.add(new_movement)
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'Pedido atualizado com sucesso.'})

        except Exception as e:
            db.session.rollback()
            print(f"Erro ao editar pedido: {e}")
            return jsonify({'success': False, 'message': 'Ocorreu um erro inesperado.'}), 500

    # GET request - retorna os dados completos do pedido para o modal de edição
    items_list = []
    for item in order.items:
        items_list.append({
            'id': item.id,
            'product_id': item.product.id,
            'name': item.product.name,
            'price': float(item.product.price),
            'quantity': item.quantity,
            'notes': item.notes if item.notes else ''
        })

    return jsonify({
        'success': True,
        'order': {
            'id': order.id,
            'notes': order.notes,
            'items': items_list
        }
    })

@caixa_bp.route('/excluir_pedido/<int:order_id>', methods=['POST'])
@login_required
def excluir_pedido(order_id):
    """
    Rota para excluir um pedido de balcão.
    """
    try:
        order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
        
        CashMovement.query.filter_by(order_id=order.id).delete()
        OrderItem.query.filter_by(order_id=order.id).delete()
        
        db.session.delete(order)
        db.session.commit()
        
        flash('Pedido excluído com sucesso!', 'success')
        return jsonify({'success': True, 'message': 'Pedido excluído com sucesso.'})
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir pedido: {str(e)}', 'danger')
        return jsonify({'success': False, 'message': 'Ocorreu um erro inesperado.'}), 500

@caixa_bp.route('/imprimir_pedido/<int:order_id>', methods=['GET'])
@login_required
def imprimir_pedido(order_id):
    """
    Gera e retorna o HTML da comanda de impressão de um pedido.
    """
    order = db.session.query(Order).options(joinedload(Order.items).joinedload(OrderItem.product)).filter(
        Order.id == order_id, 
        Order.user_id == current_user.id
    ).first_or_404()
    
    items_to_print = []
    for item in order.items:
        items_to_print.append({
            'name': item.product.name,
            'quantity': item.quantity,
            'price': item.price_at_order,
            'total': item.quantity * item.price_at_order,
            'notes': item.notes
        })

    receipt_html = render_template(
        'caixa/receipt.html',
        order_id=order.id,
        timestamp=order.created_at.strftime('%d/%m/%Y %H:%M'),
        items=items_to_print,
        total_price=order.total_price,
        payment_method=order.payment_method,
        change_for=order.change_for,
        notes=order.notes
    )

    return jsonify({
        'success': True,
        'order_id': order.id,
        'receipt_html': receipt_html
    })
