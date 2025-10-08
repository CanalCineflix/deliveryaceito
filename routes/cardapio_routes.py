from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from models import db, User, Product, Order, OrderItem, OrderStatus, RestaurantConfig, Neighborhood, Restaurant
from datetime import datetime
import json
from sqlalchemy.orm import joinedload
from decimal import Decimal
from slugify import slugify # Importação necessária

cardapio_bp = Blueprint('cardapio', __name__, url_prefix='/cardapio')

def get_restaurant_status(opening_hours, manual_status):
    """
    Determina o status de funcionamento do restaurante (Aberto/Fechado/Indisponível).
    """
    
    # 1. VERIFICAÇÃO DE STATUS MANUAL (PRIORIDADE MÁXIMA)
    if manual_status == 'open':
        return 'Aberto'
    if manual_status == 'closed':
        return 'Fechado'
    
    # 2. VERIFICAÇÃO DE HORÁRIO AUTOMÁTICO
    if not opening_hours:
        return 'Fechado' 

    now = datetime.now()
    day_of_week = now.strftime('%A').lower()
    current_time = now.strftime('%H:%M')

    if day_of_week not in opening_hours or not opening_hours[day_of_week]:
        return 'Fechado'

    day_config = opening_hours[day_of_week]

    if not day_config.get('open'):
        return 'Fechado'

    open_time = day_config.get('open')
    close_time = day_config.get('close')

    if open_time and close_time:
        if open_time <= current_time < close_time:
            return 'Aberto'
    
    return 'Fechado'


@cardapio_bp.route('/<int:user_id>-<string:restaurant_slug>')
def menu(user_id, restaurant_slug):
    """
    Exibe o cardápio público de um restaurante.
    """
    user = User.query.get_or_404(user_id)
    
    config = user.config or RestaurantConfig(user_id=user.id)
    if not user.config:
        db.session.add(config)
        db.session.commit()

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
    
    day_names = {
        'monday': 'Segunda-feira',
        'tuesday': 'Terça-feira',
        'wednesday': 'Quarta-feira',
        'thursday': 'Quinta-feira',
        'friday': 'Sexta-feira',
        'saturday': 'Sábado',
        'sunday': 'Domingo',
    }
    
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
    order_notes = order_data.get('complement_note')
    payment_method = order_data.get('payment_method')
    change_for_str = order_data.get('change_for') # Receber como string
    neighborhood_id_str = order_data.get('neighborhood_id')
    order_items_data = order_data.get('order_items', [])

    if not all([client_name, client_phone, client_address, payment_method]):
        return jsonify({'success': False, 'message': 'Por favor, preencha todos os campos obrigatórios.'}), 400

    if not order_items_data:
        return jsonify({'success': False, 'message': 'Seu pedido não contém nenhum item.'}), 400

    try:
        # CONVERSÃO DE TIPOS CRÍTICAS PARA DECIMAL/FLOAT
        total_price = Decimal(0)
        delivery_fee = Decimal(0)
        change_for = Decimal(change_for_str) if change_for_str and change_for_str.isdigit() else None
        
        # 1. Busca e calcula Taxa de Entrega
        if neighborhood_id_str:
            try:
                neighborhood = Neighborhood.query.get(int(neighborhood_id_str))
                if neighborhood:
                    delivery_fee = Decimal(neighborhood.delivery_fee)
            except (ValueError, TypeError):
                # Se neighborhood_id for inválido, tenta pegar a taxa padrão do config
                config = RestaurantConfig.query.filter_by(user_id=user_id).first()
                if config and config.default_delivery_fee:
                     delivery_fee = Decimal(config.default_delivery_fee)
                else:
                    print("⚠️ Aviso: neighborhood_id inválido e sem default_delivery_fee.")


        new_order = Order(
            user_id=user_id,
            client_name=client_name,
            client_phone=client_phone,
            client_address=client_address,
            notes=order_notes,
            # Inicializa com 0.0, será atualizado após o loop
            total_price=0.0, 
            status=OrderStatus.PENDING,
            payment_method=payment_method,
            # Passa change_for como Decimal para o objeto
            change_for=change_for if change_for and payment_method == 'Dinheiro' else None
        )
        db.session.add(new_order)
        db.session.flush()

        # 2. Loop para salvar OrderItems
        for item_data in order_items_data:
            try:
                product_id = int(item_data.get('id'))
                quantity = int(item_data.get('quantity'))
                observation = item_data.get('note', '') # Garante que 'note' é a chave
                
                if quantity <= 0:
                    continue

                product = Product.query.get(product_id)

                if product:
                    # CORREÇÃO: Usa Decimal para o cálculo
                    item_total = Decimal(product.price) * Decimal(quantity)
                    total_price += item_total

                    new_item = OrderItem(
                        order_id=new_order.id,
                        product_id=product.id,
                        quantity=quantity,
                        price_at_order=product.price,
                        notes=observation
                    )
                    db.session.add(new_item)
                
            except (ValueError, TypeError) as e:
                # Loga o item que falhou, mas continua o loop
                print(f"⚠️ Erro ao processar item {item_data}: {e}")
                continue

        # 3. Cálculo Final e Troco
        final_total = total_price + delivery_fee
        new_order.total_price = float(final_total) # Salva como float no DB
        new_order.delivery_fee = float(delivery_fee) # Salva como float no DB

        if new_order.payment_method == 'Dinheiro' and new_order.change_for is not None:
            # Troco a ser devolvido = Troco para - Total
            troco_a_devolver = new_order.change_for - final_total
            new_order.change_due = float(troco_a_devolver) # Salva como float no DB
            print(f"Valor do troco a ser devolvido: {new_order.change_due}")
        
        db.session.commit()
        
        return jsonify({'success': True, 'redirect_url': url_for('cardapio.order_confirmation', order_id=new_order.id)}), 200

    except Exception as e:
        db.session.rollback()
        # Loga o erro detalhado
        print(f"🚨 ERRO FATAL ao criar pedido: {e}")
        return jsonify({'success': False, 'message': f'Ocorreu um erro inesperado ao processar seu pedido. Por favor, tente novamente. Erro: {str(e)}'}), 500

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
    try:
        # 1. Busca o pedido e carrega os itens
        order = Order.query.options(
            joinedload(Order.items).joinedload(OrderItem.product),
            joinedload(Order.user) # Adicionado para garantir acesso ao nome do restaurante
        ).filter_by(id=order_id).first_or_404()
        
        restaurant_user = order.user
        
        # 2. Geração do Slug (Corrige o erro de "carregar confirmação")
        
        # O nome real do restaurante deve vir do modelo 'Restaurant' ou 'User'
        # Assumindo que o nome do restaurante está em 'restaurant_name' no User ou modelo relacionado.
        # Fallback para o nome do restaurante conforme o seu perfil
        restaurant_name = getattr(restaurant_user, 'restaurant_name', 'Restaurante Teste hauss') 
        
        # Se você tem um modelo Restaurant associado (o que seria ideal), use ele:
        # restaurant_name = order.user.restaurant.name 
        
        base_slug = slugify(restaurant_name)
        final_slug = f"{order.user_id}-{base_slug}"

        # 3. Calcula o troco (caso não tenha sido salvo corretamente no create_order)
        # O cálculo deve ser feito no create_order, mas é bom ter o fallback aqui.
        order.change_due = 0.0
        if order.payment_method == 'Dinheiro' and order.change_for is not None and order.total_price is not None:
             order.change_due = order.change_for - order.total_price

        # 4. Renderiza, passando o slug completo
        return render_template(
            'cardapio/order_confirmation.html',
            order=order,
            restaurant_slug=final_slug # Passa o slug COMPLETO
        )

    except Exception as e:
        # Log do erro para debug
        print(f"⚠️ ERRO em order_confirmation: {e}")
        # Aborta com um erro interno, para que o erro seja logado no Render
        abort(500, description=f"Erro ao carregar confirmação do pedido: {e}") 
        # Alternativamente, a mensagem simples que você já tem:
        # return "Erro ao carregar confirmação do pedido.", 500
