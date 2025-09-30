import os
import json
# Importação adicionada para criar slugs (nomes amigáveis para URL)
from slugify import slugify
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, abort
from flask_login import login_required, current_user
from models import db, User, Product, Neighborhood, RestaurantConfig, Restaurant

perfil_bp = Blueprint('perfil', __name__, url_prefix='/perfil')

# --- NOVA FUNÇÃO: OBTÉM A URL BASE DINAMICAMENTE (Render ou Local) ---
def get_base_url():
    """Determina a URL base da aplicação (Produção no Render ou Desenvolvimento local)."""
    # A variável de ambiente RENDER é definida automaticamente pelo Render.
    if os.environ.get('RENDER'):
        # URL de Produção. Usamos o cabeçalho 'X-Forwarded-Host' que o Render fornece.
        # RENDER_EXTERNAL_HOSTNAME é uma alternativa segura.
        host = request.headers.get('X-Forwarded-Host') or os.environ.get('RENDER_EXTERNAL_HOSTNAME')
        # Sempre HTTPS no Render
        return f"https://{host}"
    else:
        # URL de Desenvolvimento local (usando o host atual da requisição).
        # Pode ser HTTP ou HTTPS dependendo da sua configuração local
        return f"{request.scheme}://{request.host}"
# --------------------------------------------------------------------------

def allowed_file(filename):
    """Verifica se a extensão do arquivo é permitida."""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'jfif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@perfil_bp.route('/')
@login_required
def index():
    """
    Rota principal da página de perfil do usuário.
    Carrega e passa todos os dados necessários para o template, incluindo o link dinâmico.
    """
    # Garante que o usuário tenha uma configuração associada
    config = current_user.config or RestaurantConfig(user_id=current_user.id)
    if not current_user.config:
        db.session.add(config)
        db.session.commit()

    # --- LÓGICA DE GERAÇÃO DO LINK DINÂMICO ---
    
    # 1. Carrega o nome do restaurante
    # Garante que 'restaurants' seja tratado corretamente (relacionamento one-to-one/many-to-one)
    restaurant = current_user.restaurants if hasattr(current_user, 'restaurants') and current_user.restaurants else None
    restaurant_name = restaurant.name if restaurant and restaurant.name else 'N/A'
    
    # 2. Cria o SLUG (nome amigável na URL) a partir do nome. 
    slug_name = slugify(restaurant_name)
    
    # 3. Obtém a URL base (Render ou Local)
    base_url = get_base_url()

    # 4. Monta o Link do Cardápio no formato: [URL_BASE]/cardapio/[ID]-[SLUG]
    menu_link = f"{base_url}/cardapio/{current_user.id}-{slug_name}"
    
    # --- FIM DA LÓGICA DE GERAÇÃO DO LINK ---


    def load_json_with_fallback(json_string, fallback_value):
        try:
            return json.loads(json_string) if json_string and json_string.strip() else fallback_value
        except (json.JSONDecodeError, TypeError):
            return fallback_value

    user_data = {
        'restaurant_name': restaurant_name,
        'whatsapp': current_user.whatsapp,
        'address': config.address,
        'logo_url': config.logo_url,
    }

    opening_hours = load_json_with_fallback(config.business_hours, {})
    manual_status_override = config.manual_status_override

    user_neighborhoods = Neighborhood.query.filter_by(user_id=current_user.id).all()
    user_products = Product.query.filter_by(user_id=current_user.id).all()

    return render_template(
        'perfil/index.html',
        menu_link=menu_link,
        user_data=user_data,
        neighborhoods=user_neighborhoods,
        products=user_products,
        opening_hours=opening_hours,
        manual_status_override=manual_status_override,
        current_user=current_user
    )

# Rota para atualização de perfil (Lógica básica adicionada)
@perfil_bp.route('/editar', methods=['POST'])
@login_required
def update_profile():
    """Atualiza dados básicos do restaurante (nome e whatsapp) e da configuração (endereço, logo)."""
    try:
        # 1. Busca ou cria RestaurantConfig
        config = current_user.config or RestaurantConfig(user_id=current_user.id)
        if not current_user.config:
            db.session.add(config)
        
        # 2. Atualiza dados na tabela User (WhatsApp)
        current_user.whatsapp = request.form.get('whatsapp')

        # 3. Atualiza dados na tabela Restaurant (Nome, se existir)
        restaurant = current_user.restaurants
        if restaurant:
            restaurant.name = request.form.get('restaurant_name')

        # 4. Atualiza dados na tabela RestaurantConfig (Endereço, Logo URL)
        config.address = request.form.get('address')
        
        # Lógica simplificada de upload/URL de logo (APENAS URL para este exemplo)
        logo_url = request.form.get('logo_url')
        if logo_url:
             config.logo_url = logo_url

        db.session.commit()
        flash('Perfil atualizado com sucesso!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar perfil: {e}', 'error')
        current_app.logger.error(f"Erro ao atualizar perfil do usuário {current_user.id}: {e}")
    
    return redirect(url_for('perfil.index'))


# Rota para atualização de horários de funcionamento (Lógica completa implementada)
@perfil_bp.route('/update-hours', methods=['POST'])
@login_required
def update_hours():
    """
    Salva os horários de funcionamento (business_hours) do restaurante como JSON string.
    Espera um payload JSON no corpo da requisição.
    """
    if request.is_json:
        try:
            # 1. Recebe o objeto de horários (espera um dicionário Python)
            hours_data = request.json
            
            # 2. Validação simples para garantir que é um objeto válido
            if not isinstance(hours_data, dict):
                return jsonify({'success': False, 'message': 'Payload inválido. Esperado um objeto JSON.'}), 400

            # 3. Busca ou cria RestaurantConfig
            config = current_user.config or RestaurantConfig(user_id=current_user.id)
            if not current_user.config:
                db.session.add(config)
            
            # 4. Converte o dicionário de horários para JSON string
            config.business_hours = json.dumps(hours_data)
            
            # 5. Salva no banco de dados
            db.session.commit()
            return jsonify({'success': True, 'message': 'Horários de funcionamento atualizados com sucesso.'}), 200

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao atualizar horários: {e}")
            return jsonify({'success': False, 'message': f'Erro interno ao salvar horários: {str(e)}'}), 500
    else:
        return jsonify({'success': False, 'message': 'Requisição deve ser JSON.'}), 400


# Rota para atualizar o status manual (Lógica completa implementada)
@perfil_bp.route('/update-status', methods=['POST'])
@login_required
def update_status():
    """
    Atualiza o override manual do status de abertura (manual_status_override).
    Espera um valor booleano (true/false) para 'is_open' e 'manual_override' no corpo JSON.
    """
    if request.is_json:
        try:
            data = request.json
            manual_override = data.get('manual_override', False)
            is_open = data.get('is_open', False)

            # O valor a ser salvo na coluna 'manual_status_override' será:
            # 1. 'open' se o override estiver ligado E o status for 'aberto'.
            # 2. 'closed' se o override estiver ligado E o status for 'fechado'.
            # 3. None se o override estiver desligado (Modo Automático).
            new_status = None
            if manual_override:
                new_status = 'open' if is_open else 'closed'

            # LOG DE CONFIRMAÇÃO: Mostra o que será salvo no banco de dados.
            print(f"--- LOG STATUS: Tentando salvar manual_status_override como: '{new_status}' ---")

            # 1. Busca ou cria RestaurantConfig
            config = current_user.config or RestaurantConfig(user_id=current_user.id)
            if not current_user.config:
                db.session.add(config)

            # 2. Atualiza o status
            config.manual_status_override = new_status
            
            # 3. Salva no banco de dados
            db.session.commit()
            
            status_message = "Modo Automático Ativado."
            if new_status == 'open':
                status_message = "Status Manual: Aberto."
            elif new_status == 'closed':
                status_message = "Status Manual: Fechado."

            # LOG DE SUCESSO
            print(f"--- LOG STATUS: Sucesso! Novo status no DB: '{new_status}' ---")

            return jsonify({'success': True, 'message': status_message, 'current_override': new_status}), 200

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao atualizar status: {e}")
            return jsonify({'success': False, 'message': f'Erro interno ao salvar status: {str(e)}'}), 500
    else:
        return jsonify({'success': False, 'message': 'Requisição deve ser JSON.'}), 400


@perfil_bp.route('/senha', methods=['POST'])
@login_required
def update_password():
    # ...
    pass # Placeholder para evitar IndentationError

@perfil_bp.route('/add_neighborhood', methods=['POST'])
@login_required
def add_neighborhood():
    # ...
    pass # Placeholder para evitar IndentationError

@perfil_bp.route('/delete_neighborhood/<int:neighborhood_id>', methods=['GET'])
@login_required
def delete_neighborhood(neighborhood_id):
    # ...
    pass # Placeholder para evitar IndentationError

@perfil_bp.route('/produtos/novo', methods=['POST'])
@login_required
def add_product():
    # ...
    pass # Placeholder para evitar IndentationError

@perfil_bp.route('/produtos/<int:product_id>/editar', methods=['POST'])
@login_required
def edit_product(product_id):
    # ...
    pass # Placeholder para evitar IndentationError

@perfil_bp.route('/excluir/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    # ...
    pass # Placeholder para evitar IndentationError

@perfil_bp.route('/produtos/toggle_status/<int:product_id>', methods=['POST'])
@login_required
def toggle_product_status(product_id):
    # ...
    pass # Placeholder para evitar IndentationError

@perfil_bp.route('/produtos')
@login_required
def products():
    user_products = Product.query.filter_by(user_id=current_user.id).all()
    return render_template('perfil/products.html', products=user_products)
