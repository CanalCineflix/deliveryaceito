# routes/produtos_routes.py
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models import db, Product # Assumindo que o modelo Product está no arquivo models.py
from werkzeug.utils import secure_filename
from forms import ProductForm # Você precisará criar este formulário futuramente

# Criação do Blueprint para as rotas de produtos
produtos_bp = Blueprint('produtos', __name__, url_prefix='/produtos')

# Função auxiliar para validar extensões de arquivo
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@produtos_bp.route('/')
@login_required
def index():
    """
    Rota principal da gestão de produtos.
    Exibe a lista de todos os produtos do usuário logado.
    """
    products = Product.query.filter_by(user_id=current_user.id).order_by(Product.name).all()
    return render_template('perfil/products.html', products=products)

@produtos_bp.route('/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar():
    """
    Rota para adicionar um novo produto.
    """
    form = ProductForm()
    if form.validate_on_submit():
        file = form.photo.data
        filename = None
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', str(current_user.id))
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)
        
        # Cria um novo produto com os dados do formulário
        new_product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            category=form.category.data,
            is_delivery=form.is_delivery.data,
            is_balcao=form.is_balcao.data,
            user_id=current_user.id,
            photo_url=url_for('static', filename=f'uploads/{current_user.id}/{filename}') if filename else None
        )
        
        db.session.add(new_product)
        db.session.commit()
        flash('Produto adicionado com sucesso!', 'success')
        return redirect(url_for('produtos.index'))
        
    return render_template('produtos/adicionar.html', form=form)

@produtos_bp.route('/editar/<int:product_id>', methods=['GET', 'POST'])
@login_required
def editar(product_id):
    """
    Rota para editar um produto existente.
    """
    product = Product.query.filter_by(id=product_id, user_id=current_user.id).first_or_404()
    form = ProductForm(obj=product)

    if request.method == 'POST':
        form.process(formdata=request.form, obj=product)
        
        # Atualiza os dados do produto com base no formulário
        product.name = form.name.data
        product.description = form.description.data
        product.price = form.price.data
        product.category = form.category.data
        product.is_delivery = form.is_delivery.data
        product.is_balcao = form.is_balcao.data
        
        file = request.files.get('photo')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', str(current_user.id))
            file_path = os.path.join(upload_folder, filename)
            
            # Remove a foto antiga se houver
            if product.photo_url:
                old_filename = os.path.basename(product.photo_url)
                old_file_path = os.path.join(upload_folder, old_filename)
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)

            file.save(file_path)
            product.photo_url = url_for('static', filename=f'uploads/{current_user.id}/{filename}')
        elif file.filename != '':
            flash('Tipo de arquivo não permitido.', 'danger')
            return render_template('produtos/editar.html', form=form, product=product)

    db.session.commit()
    flash('Produto atualizado com sucesso!', 'success')
    return redirect(url_for('produtos.index'))

@produtos_bp.route('/toggle-delivery/<int:product_id>', methods=['POST'])
@login_required
def toggle_delivery(product_id):
    """
    Alterna o status de delivery de um produto.
    """
    product = Product.query.filter_by(id=product_id, user_id=current_user.id).first_or_404()
    product.is_delivery = not product.is_delivery
    db.session.commit()
    flash('Status de delivery do produto atualizado com sucesso!', 'success')
    return redirect(url_for('produtos.index'))

@produtos_bp.route('/toggle-balcao/<int:product_id>', methods=['POST'])
@login_required
def toggle_balcao(product_id):
    """
    Alterna o status de balcão de um produto.
    """
    product = Product.query.filter_by(id=product_id, user_id=current_user.id).first_or_404()
    product.is_balcao = not product.is_balcao
    db.session.commit()
    flash('Status de balcão do produto atualizado com sucesso!', 'success')
    return redirect(url_for('produtos.index'))

@produtos_bp.route('/excluir/<int:product_id>', methods=['POST'])
@login_required
def excluir(product_id):
    """
    Rota para excluir um produto.
    """
    product = Product.query.filter_by(id=product_id, user_id=current_user.id).first_or_404()
    
    # Remove a foto do servidor se ela existir
    if product.photo_url:
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', str(current_user.id))
        filename = os.path.basename(product.photo_url)
        file_path = os.path.join(upload_folder, filename)
        if os.path.exists(file_path):
            os.remove(file_path)

    db.session.delete(product)
    db.session.commit()
    flash('Produto excluído com sucesso!', 'success')
    return redirect(url_for('produtos.index'))
