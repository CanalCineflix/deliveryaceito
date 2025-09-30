import os
import json
from slugify import slugify # Adicionado: Necessário para criar URLs amigáveis
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, abort
from flask_login import login_required, current_user
from models import db, User, Product, Neighborhood, RestaurantConfig, Restaurant

perfil_bp = Blueprint('perfil', __name__, url_prefix='/perfil')

def allowed_file(filename):
    """Verifica se a extensão do arquivo é permitida."""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'jfif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_base_url():
    """Determina a URL base da aplicação (Render ou Local)."""
    if os.environ.get('RENDER'):
        # Tenta usar o cabeçalho X-Forwarded-Host (mais comum) ou a variável do Render
        host = request.headers.get('X-Forwarded-Host') or os.environ.get('RENDER_EXTERNAL_HOSTNAME')
        # Garantindo que a URL é HTTPS em produção
        return f"https://{host}" if host else f"{request.scheme}://{request.host}"
    else:
        # Usa localhost para desenvolvimento
        return f"{request.scheme}://{request.host}"

def load_json_with_fallback(json_string, fallback_value):
    """Carrega JSON de forma segura."""
    try:
        return json.loads(json_string) if json_string and json_string.strip() else fallback_value
    except (json.JSONDecodeError, TypeError):
        return fallback_value

@perfil_bp.route('/')
@login_required
def index():
    """
    Rota principal da página de perfil do usuário.
    Carrega e passa todos os dados necessários para o template.
    """
    config = current_user.config or RestaurantConfig(user_id=current_user.id)
    if not current_user.config:
        db.session.add(config)
        db.session.commit()

    # VERIFICA O NOME DO RESTAURANTE ATRAVÉS DA RELAÇÃO COM O MODELO 'RESTAURANT'
    restaurant = current_user.restaurants
    restaurant_name = restaurant.name if restaurant and restaurant.name else 'N/A'
    
    # CRIAÇÃO CORRETA DO LINK DO CARDÁPIO USANDO SLUG
    slug_name = slugify(restaurant_name)
    base_url = get_base_url()
    menu_link = f"{base_url}/cardapio/{current_user.id}-{slug_name}"


    user_data = {
        'restaurant_name': restaurant_name,
        'whatsapp': current_user.whatsapp,
        'address': config.address,
        'logo_url': config.logo_url,
    }

    opening_hours = load_json_with_fallback(config.business_hours, {})
    # O status deve ser lido aqui para ser passado ao template e ao JavaScript
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

@perfil_bp.route('/editar', methods=['POST'])
@login_required
def update_profile():
    """
    Rota para atualizar os dados básicos e a logo do restaurante.
    """
    try:
        config = current_user.config
        if not config:
            config = RestaurantConfig(user_id=current_user.id)
            db.session.add(config)
        
        # O NOME DO RESTAURANTE DEVE SER ATUALIZADO VIA O OBJETO RESTAURANT
        restaurant = current_user.restaurants
        restaurant_name_form = request.form.get('restaurant_name')

        if restaurant:
            restaurant.name = restaurant_name_form
        else:
            # Cria um novo restaurante se ele não existir
            new_restaurant = Restaurant(user_id=current_user.id, name=restaurant_name_form)
            db.session.add(new_restaurant)

        current_user.whatsapp = request.form.get('whatsapp')
        config.address = request.form.get('address')

        if 'logo' in request.files:
            file = request.files['logo']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                
                logo_path = os.path.join(upload_folder, f"{current_user.id}_{filename}")
                file.save(logo_path)
                config.logo_url = url_for('static', filename=f"uploads/{current_user.id}_{filename}")

        db.session.commit()
        flash('Perfil atualizado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar o perfil: {str(e)}', 'danger')
        current_app.logger.error(f"Erro ao atualizar perfil: {e}")
    
    return redirect(url_for('perfil.index'))

@perfil_bp.route('/update-hours', methods=['POST'])
@login_required
def update_hours():
    """
    Rota para atualizar os horários de funcionamento do restaurante.
    """
    if not request.is_json:
        return jsonify({'success': False, 'message': 'Requisição deve ser JSON.'}), 400

    try:
        hours_data = request.json
        if not isinstance(hours_data, dict):
            return jsonify({'success': False, 'message': 'Payload inválido. Esperado um objeto JSON.'}), 400

        config = current_user.config
        if not config:
            config = RestaurantConfig(user_id=current_user.id)
            db.session.add(config)
        
        # O frontend da rota 'update-hours' (que não está aqui) deve estar enviando um JSON
        # diferente do que a rota de perfil esperava (que usava request.form). 
        # Mantendo a lógica de processamento de JSON para a rota update-hours:
        config.business_hours = json.dumps(hours_data)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Horários de funcionamento atualizados com sucesso.'}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao atualizar horários: {e}")
        return jsonify({'success': False, 'message': f'Erro interno ao salvar horários: {str(e)}'}), 500


# Rota de Status CRÍTICA para o seu problema. 
@perfil_bp.route('/update-status', methods=['POST'])
@login_required
def update_status():
    """
    Atualiza o override manual do status de abertura (manual_status_override).
    Espera um valor de 'status' no corpo JSON: 'open', 'closed' ou 'auto'.
    """
    if request.is_json:
        try:
            data = request.json
            new_status = data.get('status')
            
            # 1. Checagem de valor válido
            if new_status not in ['auto', 'open', 'closed']:
                return jsonify({'success': False, 'message': 'Status de override inválido.'}), 400

            # --- LOG DE DIAGNÓSTICO (RECEBIDO) ---
            print(f"--- LOG STATUS (RECEBIDO) ---")
            print(f"Status recebido do Frontend: '{new_status}'")
            
            # 2. Busca ou cria RestaurantConfig
            config = current_user.config or RestaurantConfig(user_id=current_user.id)
            if not current_user.config:
                db.session.add(config)
                print(f"Aviso: Configuração criada na hora para o usuário {current_user.id}")

            # 3. Atualiza e Salva
            config.manual_status_override = new_status if new_status != 'auto' else None
            db.session.commit()
            
            # --- LOG DE SUCESSO ---
            print(f"Novo status no DB CONFIRMADO: '{config.manual_status_override}'")
            print(f"------------------------------")
            
            status_message = "Status Manual Desativado (Modo Automático)."
            if new_status == 'open':
                status_message = "Status Manual: Aberto."
            elif new_status == 'closed':
                status_message = "Status Manual: Fechado."

            return jsonify({'success': True, 'message': status_message, 'current_override': config.manual_status_override or 'auto'}), 200

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"ERRO AO ATUALIZAR STATUS MANUAL: {e}")
            # --- LOG DE ERRO CRÍTICO ---
            print(f"--- LOG STATUS (FALHA) ---")
            print(f"ERRO CRÍTICO no DB: {str(e)}")
            print(f"---------------------------")
            return jsonify({'success': False, 'message': f'Erro interno ao salvar status: {str(e)}'}), 500
    else:
        return jsonify({'success': False, 'message': 'Requisição deve ser JSON.'}), 400

# Rotas restantes (mantidas para integridade do arquivo)

@perfil_bp.route('/senha', methods=['POST'])
@login_required
def change_password():
    """Altera a senha do usuário."""
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not current_user.check_password(current_password):
        flash('Senha atual incorreta.', 'danger')
        return redirect(url_for('perfil.index'))
    
    if new_password != confirm_password:
        flash('As novas senhas não coincidem.', 'danger')
        return redirect(url_for('perfil.index'))
    
    current_user.set_password(new_password)
    db.session.commit()
    
    flash('Senha alterada com sucesso!', 'success')
    return redirect(url_for('perfil.index'))

@perfil_bp.route('/add_neighborhood', methods=['POST'])
@login_required
def add_neighborhood():
    """Adiciona um novo bairro de entrega."""
    name = request.form.get('name')
    delivery_fee_str = request.form.get('delivery_fee')

    if name and delivery_fee_str:
        try:
            delivery_fee = float(delivery_fee_str.replace(',', '.'))
            
            new_neighborhood = Neighborhood(
                user_id=current_user.id,
                name=name,
                delivery_fee=delivery_fee
            )

            db.session.add(new_neighborhood)
            db.session.commit()
            
            flash(f'Bairro "{name}" adicionado com sucesso!', 'success')
        except (ValueError, TypeError):
            flash('Taxa de entrega inválida. Use apenas números.', 'danger')
    else:
        flash('Nome do bairro e taxa de entrega são obrigatórios.', 'danger')

    return redirect(url_for('perfil.index'))

@perfil_bp.route('/delete_neighborhood/<int:neighborhood_id>', methods=['GET'])
@login_required
def delete_neighborhood(neighborhood_id):
    """Remove um bairro de entrega."""
    neighborhood_to_delete = Neighborhood.query.filter_by(
        id=neighborhood_id, 
        user_id=current_user.id
    ).first()
    
    if neighborhood_to_delete:
        db.session.delete(neighborhood_to_delete)
        db.session.commit()
        flash(f'Bairro "{neighborhood_to_delete.name}" removido.', 'success')
    else:
        flash('Bairro não encontrado.', 'danger')
    
    return redirect(url_for('perfil.index'))

@perfil_bp.route('/produtos/novo', methods=['POST'])
@login_required
def add_product():
    """Adiciona um novo produto ao cardápio."""
    name = request.form.get('name')
    description = request.form.get('description', '')
    price_str = request.form.get('price')
    category = request.form.get('category', '')
    photo_url = None

    if not name or not price_str:
        flash('Nome e preço do produto são obrigatórios.', 'danger')
        return redirect(url_for('perfil.products'))

    try:
        price = float(price_str.strip().replace(',', '.'))
        
        if 'photo' in request.files:
            file = request.files['photo']
            
            # LINHAS DE DEBBUG
            print(f"Arquivo recebido: {file.filename}")
            print(f"Nome do arquivo seguro: {secure_filename(file.filename)}")
            
            if file and allowed_file(file.filename):
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', str(current_user.id))
                os.makedirs(upload_folder, exist_ok=True)
                
                filename = secure_filename(file.filename)
                file_path = os.path.join(upload_folder, filename)
                
                # LINHAS DE DEBBUG
                print(f"Caminho completo do arquivo: {file_path}")
                
                file.save(file_path)
                
                # LINHAS DE DEBBUG
                if os.path.exists(file_path):
                    print("SUCESSO: O arquivo foi salvo no caminho.")
                else:
                    print("ERRO: O arquivo NÃO foi salvo.")

                photo_url = url_for('static', filename=f'uploads/{current_user.id}/{filename}')

        product = Product(
            user_id=current_user.id,
            name=name,
            description=description,
            price=price,
            category=category,
            photo_url=photo_url,
            is_active=True
        )
        db.session.add(product)
        db.session.commit()
        flash('Produto adicionado com sucesso!', 'success')
    except (ValueError, TypeError) as e:
        # LINHA DE DEBBUG
        print(f"ERRO NA CONVERSÃO DO PREÇO: {e}")
        flash('Preço do produto inválido. Use apenas números, com ponto ou vírgula para decimais.', 'danger')
    
    return redirect(url_for('perfil.products'))

@perfil_bp.route('/produtos/<int:product_id>/editar', methods=['POST'])
@login_required
def update_product(product_id):
    """Atualiza um produto existente."""
    product = Product.query.filter_by(id=product_id, user_id=current_user.id).first()
    if not product:
        flash('Produto não encontrado.', 'danger')
        return redirect(url_for('perfil.products'))

    try:
        product.name = request.form.get('name')
        product.description = request.form.get('description', '')
        # CORREÇÃO: Substitui a vírgula por ponto antes de converter para float
        product.price = float(request.form.get('price').replace(',', '.'))
        product.category = request.form.get('category', '')
        
        # Lógica para atualizar a foto do produto
        if 'photo' in request.files:
            file = request.files['photo']
            if file and allowed_file(file.filename):
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', str(current_user.id))
                os.makedirs(upload_folder, exist_ok=True)
                
                filename = secure_filename(file.filename)
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
                product.photo_url = url_for('static', filename=f'uploads/{current_user.id}/{filename}')

        db.session.commit()
        flash(f'Produto "{product.name}" atualizado com sucesso!', 'success')
    except (ValueError, TypeError):
        db.session.rollback()
        flash('Erro ao atualizar o produto. Verifique os dados.', 'danger')

    return redirect(url_for('perfil.products'))

@perfil_bp.route('/excluir/<int:product_id>', methods=['POST'])
@login_required
def excluir(product_id):
    """Exclui um produto do cardápio."""
    product_to_delete = Product.query.filter_by(id=product_id, user_id=current_user.id).first_or_404()

    db.session.delete(product_to_delete)
    db.session.commit()

    flash('Produto excluído com sucesso!', 'danger')
    return redirect(url_for('perfil.products'))


@perfil_bp.route('/produtos/toggle_status/<int:product_id>', methods=['POST'])
@login_required
def toggle_product_status(product_id):
    """
    Alterna o status de ativo/inativo de um produto.
    """
    product = Product.query.filter_by(id=product_id, user_id=current_user.id).first_or_404()
    
    product.is_active = not product.is_active
    db.session.commit()
    
    flash(f'Status do produto "{product.name}" atualizado para {"Ativo" if product.is_active else "Inativo"}.', 'success')
    return redirect(url_for('perfil.products'))

@perfil_bp.route('/produtos')
@login_required
def products():
    user_products = Product.query.filter_by(user_id=current_user.id).all()
    return render_template('perfil/products.html', products=user_products)
