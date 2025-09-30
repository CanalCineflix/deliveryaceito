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
    config = current_user.config or RestaurantConfig(user_id=current_user.id)
    if not current_user.config:
        db.session.add(config)
        db.session.commit()

    # --- LÓGICA DE GERAÇÃO DO LINK DINÂMICO ---
    
    # 1. Carrega o nome do restaurante
    restaurant = current_user.restaurants
    restaurant_name = restaurant.name if restaurant and restaurant.name else 'N/A'
    
    # 2. Cria o SLUG (nome amigável na URL) a partir do nome. 
    # Usamos o ID do usuário como fallback se o nome for 'N/A'.
    # O slug deve ser único e amigável.
    slug_name = slugify(restaurant_name)
    
    # 3. Obtém a URL base (Render ou Local)
    base_url = get_base_url()

    # 4. Monta o Link do Cardápio no formato: [URL_BASE]/cardapio/[ID]-[SLUG]
    # Se o nome for 'N/A', o slug será 'n-a', mas o ID garante a unicidade.
    # Ex: https://deliveryaceito.onrender.com/cardapio/123-o-rappa-anjos-gourmet
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
        menu_link=menu_link, # ESTA VARIÁVEL AGORA TEM A URL COMPLETA E DINÂMICA
        user_data=user_data,
        neighborhoods=user_neighborhoods,
        products=user_products,
        opening_hours=opening_hours,
        manual_status_override=manual_status_override,
        # Mantendo 'current_user' diretamente para acesso a outros campos, se necessário
        current_user=current_user
    )

# ... (O restante das suas rotas continua abaixo, sem alterações) ...
@perfil_bp.route('/editar', methods=['POST'])
@login_required
def update_profile():
# ...
@perfil_bp.route('/update-hours', methods=['POST'])
# ...
@perfil_bp.route('/update-status', methods=['POST'])
# ...
@perfil_bp.route('/senha', methods=['POST'])
# ...
@perfil_bp.route('/add_neighborhood', methods=['POST'])
# ...
@perfil_bp.route('/delete_neighborhood/<int:neighborhood_id>', methods=['GET'])
# ...
@perfil_bp.route('/produtos/novo', methods=['POST'])
# ...
@perfil_bp.route('/produtos/<int:product_id>/editar', methods=['POST'])
# ...
@perfil_bp.route('/excluir/<int:product_id>', methods=['POST'])
# ...
@perfil_bp.route('/produtos/toggle_status/<int:product_id>', methods=['POST'])
# ...
@perfil_bp.route('/produtos')
@login_required
def products():
    user_products = Product.query.filter_by(user_id=current_user.id).all()
    return render_template('perfil/products.html', products=user_products)
