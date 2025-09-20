import os
import json
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

    menu_link = f"http://localhost:5000/cardapio/{current_user.id}"

    def load_json_with_fallback(json_string, fallback_value):
        try:
            return json.loads(json_string) if json_string and json_string.strip() else fallback_value
        except (json.JSONDecodeError, TypeError):
            return fallback_value

    # VERIFICA O NOME DO RESTAURANTE ATRAVÉS DA RELAÇÃO COM O MODELO 'RESTAURANT'
    # E PEGA O NOME OU USA 'N/A' COMO PADRÃO
    restaurant = current_user.restaurants
    restaurant_name = restaurant.name if restaurant else 'N/A'

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
        # Mantendo 'current_user' diretamente para acesso a outros campos, se necessário
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
        if restaurant:
            restaurant.name = request.form.get('restaurant_name')
        else:
            # Cria um novo restaurante se ele não existir
            new_restaurant = Restaurant(user_id=current_user.id, name=request.form.get('restaurant_name'))
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
    
    return redirect(url_for('perfil.index'))

@perfil_bp.route('/update-hours', methods=['POST'])
@login_required
def update_hours():
    """
    Rota para atualizar os horários de funcionamento do restaurante.
    """
    try:
        config = current_user.config
        if not config:
            config = RestaurantConfig(user_id=current_user.id)
            db.session.add(config)

        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        new_hours = {}
        for day in days:
            is_closed = request.form.get(f'{day}_closed')
            if is_closed == 'on':
                new_hours[day] = {}
            else:
                open_time = request.form.get(f'{day}_open')
                close_time = request.form.get(f'{day}_close')
                if open_time and close_time:
                    new_hours[day] = {'open': open_time, 'close': close_time}
        
        config.business_hours = json.dumps(new_hours)
        db.session.commit()
        
        flash('Horários atualizados com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar os horários: {str(e)}', 'danger')
    
    return redirect(url_for('perfil.index'))

@perfil_bp.route('/update-status', methods=['POST'])
@login_required
def update_status():
    """
    Rota para atualizar o status manual do restaurante (via AJAX).
    """
    config = current_user.config
    if not config:
        return jsonify({'success': False, 'message': 'Configuração do restaurante não encontrada.'}), 404

    data = request.get_json()
    new_status = data.get('status')

    if new_status in ['auto', 'open', 'closed']:
        config.manual_status_override = new_status
        db.session.commit()
        return jsonify({'success': True, 'status': new_status})
    
    return jsonify({'success': False, 'message': 'Status inválido.'}), 400

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
