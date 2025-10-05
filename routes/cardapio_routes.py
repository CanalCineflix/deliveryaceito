from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from models import db, User, Product, Order, OrderItem, OrderStatus, RestaurantConfig, Neighborhood, Restaurant
from datetime import datetime
import json
from sqlalchemy.orm import joinedload
from decimal import Decimal

cardapio_bp = Blueprint('cardapio', __name__, url_prefix='/cardapio')

def get_restaurant_status(opening_hours, manual_status):
    """
    Determina o status de funcionamento do restaurante (Aberto/Fechado/Indisponível).
    
    O status manual (manual_status) tem prioridade absoluta.
    Ele é definido como 'open' ou 'closed' no perfil.
    """
    
    # 1. VERIFICAÇÃO DE STATUS MANUAL (PRIORIDADE MÁXIMA)
    if manual_status == 'open':
        return 'Aberto'
    if manual_status == 'closed':
        return 'Fechado'
    
    # 2. VERIFICAÇÃO DE HORÁRIO AUTOMÁTICO
    
    # Se não houver horário configurado e não houver status manual, é 'Fechado'
    if not opening_hours:
        return 'Fechado' 

    # Obtém o horário atual
    now = datetime.now()
    day_of_week = now.strftime('%A').lower()
    current_time = now.strftime('%H:%M')

    # Verifica se o dia atual está configurado nos horários
    if day_of_week not in opening_hours or not opening_hours[day_of_week]:
        return 'Fechado'

    day_config = opening_hours[day_of_week]

    # Verifica se o dia está explicitamente marcado como fechado ('open': false)
    if not day_config.get('open'):
        return 'Fechado'

    # Verifica os horários
    open_time = day_config.get('open')
    close_time = day_config.get('close')

    # Se os horários de abertura e fechamento existirem
    if open_time and close_time:
        # Verifica se o horário atual está entre o horário de abertura e fechamento
        if open_time <= current_time < close_time:
            return 'Aberto'
    
    # Se passou por todas as verificações automáticas e não abriu
    return 'Fechado'


@cardapio_bp.route('/<int:user_id>-<string:restaurant_slug>')
def menu(user_id, restaurant_slug):
    """
    Exibe o cardápio público de um restaurante.
    A rota foi atualizada para aceitar o ID e o slug.
    """
    # Busca o usuário (dono do restaurante) pelo ID. O slug é usado apenas para a URL amigável.
    user = User.query.get_or_404(user_id)
    
    # Opcional: Você pode querer verificar se o slug fornecido corresponde ao nome do restaurante.
    # Ex: from slugify import slugify 
    # if slugify(user.restaurants.name) != restaurant_slug:
    #    return redirect(url_for('cardapio.menu', user_id=user_id, restaurant_slug=slugify(user.restaurants.name)))

    config = user.config or RestaurantConfig(user_id=user.id)
    if not user.config:
        db.session.add(config)
        db.session.commit()

    # Busca apenas produtos ativos E marcados para delivery
    products = Product.query.filter_by(
        user_id=user.id,
        is_active=True,
        is_delivery=True
    ).all()
    
    products_by_category = {}
    for product in products:
        if product.category not in products_by_category:
            products_by_category[product.category] = []
        products_by_category[product.category].append(product)
    
    neighborhoods = Neighborhood.query.filter_by(user_id=user.id).all()
    
    opening_hours_json = config.business_hours
    try:
        opening_hours = json.loads(opening_hours_json) if opening_hours_json else {}
    except (json.JSONDecodeError, TypeError):
        opening_hours = {}

    manual_status = config.manual_status_override
    
    # LOG DE DIAGNÓSTICO
    print(f"*** DIAGNÓSTICO CARDÁPIO ***")
    print(f"ID do Usuário: {user_id}")
    print(f"Status Manual lido do DB (manual_status_override): '{manual_status}'")
    print(f"Horários lidos (business_hours): {opening_hours}")
    
    restaurant_status = get_restaurant_status(opening_hours, manual_status)

    # LOG DE DIAGNÓSTICO FINAL
    print(f"Status Final Calculado (restaurant_status): '{restaurant_status}'")
    print(f"*****************************")


    today_day_name = datetime.now().strftime('%A').lower()
    
    # Mapeamento para exibição no frontend (se necessário)
    day_names = {
        'monday': 'Segunda-feira',
        'tuesday': 'Terça-feira',
        'wednesday': 'Quarta-feira',
        'thursday': 'Quinta-feira',
        'friday': 'Sexta-feira',
        'saturday': 'Sábado',
        'sunday': 'Domingo',
    }
    
    # Marca o dia atual como 'Hoje' para o template
    if today_day_name in day_names:
        day_names[today_day_name] = 'Hoje'

    return render_template(
        'cardapio/menu.html',
        user=user,
        products_by_category=products_by_category,
        config=config,
        neighborhoods=neighborhoods,
        opening_hours=opening_hours,
        restaurant_status=restaurant_status,
        day_names=day_names
    )

@cardapio_bp.route('/<int:user_id>/create_order', methods=['POST'])
def create_order(user_id):
    order_data = request.get_json()

    print(f"Dados do pedido recebidos: {order_data}")
    print(f"Forma de pagamento recebida: {order_data.get('payment_method')}")

    if not order_data:
        return jsonify({'success': False, 'message': 'Dados de pedido ausentes.'}), 400

    client_name = order_data.get('client_name')
    client_phone = order_data.get('client_phone')
    client_address = order_data.get('client_address')
    order_notes = order_data.get('complement_note')  # Corrigido
    payment_method = order_data.get('payment_method')
    change_for = order_data.get('change_for')
    neighborhood_id = order_data.get('neighborhood_id')
    order_items_data = order_data.get('order_items', [])

    if not all([client_name, client_phone, client_address, payment_method]):
        return jsonify({'success': False, 'message': 'Por favor, preencha todos os campos obrigatórios.'}), 400

    if not order_items_data:
        return jsonify({'success': False, 'message': 'Seu pedido não contém nenhum item.'}), 400

    try:
        total_price = 0.0
        delivery_fee = 0.0

        if neighborhood_id:
            try:
                neighborhood = Neighborhood.query.get(int(neighborhood_id))
                if neighborhood:
                    delivery_fee = neighborhood.delivery_fee
            except (ValueError, TypeError):
                config = RestaurantConfig.query.filter_by(user_id=user_id).first()
                if config:
                    # Este bloco de exceção parece estar tentando pegar uma taxa de entrega padrão
                    # (default_delivery_fee) se o neighborhood_id for inválido ou não for um número.
                    # Mantenho, mas garanto que 'config' existe.
                    delivery_fee = config.default_delivery_fee

        new_order = Order(
            user_id=user_id,
            client_name=client_name,
            client_phone=client_phone,
            client_address=client_address,
            notes=order_notes,  # Corrigido
            total_price=0.0,
            status=OrderStatus.PENDING,
            payment_method=payment_method,
            change_for=float(change_for) if change_for and payment_method == 'Dinheiro' else None
        )
        db.session.add(new_order)
        db.session.flush()

        for item_data in order_items_data:
            try:
                product_id = item_data.get('id')
                quantity = item_data.get('quantity')
                observation = item_data.get('note')

                if not all([product_id, quantity]) or int(quantity) <= 0:
                    continue

                product = Product.query.get(int(product_id))
                quantity = int(quantity)

                if product:
                    item_total = product.price * quantity
                    total_price += item_total

                    new_item = OrderItem(
                        order_id=new_order.id,
                        product_id=product.id,
                        quantity=quantity,
                        price_at_order=product.price,
                        notes=observation
                    )
                    db.session.add(new_item)
            except (ValueError, TypeError, IndexError):
                continue

        # ATUALIZAÇÕES NECESSÁRIAS:
        final_total = float(total_price) + float(delivery_fee)
        new_order.total_price = final_total
        new_order.delivery_fee = delivery_fee

        if new_order.payment_method == 'Dinheiro' and new_order.change_for:
            troco_a_devolver = new_order.change_for - final_total
            new_order.change_due = troco_a_devolver
            print(f"Valor do troco a ser devolvido: {new_order.change_due}")

        db.session.commit()
        
        # A URL de redirecionamento já está correta, mas vou manter o código completo para sua conveniência
        return jsonify({'success': True, 'redirect_url': url_for('cardapio.order_confirmation', order_id=new_order.id)}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Ocorreu um erro inesperado ao processar seu pedido. Erro: {str(e)}'}), 500

@cardapio_bp.route('/<int:order_id>/pix_payment')
def pix_payment(order_id):
    order = Order.query.get_or_404(order_id)
    user = order.user
    config = RestaurantConfig.query.filter_by(user_id=user.id).first()
    
    pix_key = config.pix_key if config and config.pix_key else 'Chave PIX não configurada.'
    
    return render_template(
        'cardapio/pix_payment.html',
        user=user,
        order=order,
        pix_key=pix_key
    )

@cardapio_bp.route('/<int:order_id>/confirmacao')
def order_confirmation(order_id):
    order = Order.query.options(
        joinedload(Order.items).joinedload(OrderItem.product)
    ).filter_by(id=order_id).first_or_404()
    
    return render_template(
        'cardapio/order_confirmation.html',
        order=order
    )
