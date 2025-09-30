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
    # Verifique o nome do template aqui: 'perfil/products.html' é o correto?
    return render_template('perfil/products.html', products=products)

@produtos_bp.route('/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar():
    """
    Rota para adicionar um novo produto.
    ADICIONADO TRATAMENTO DE ERRO CRÍTICO PARA DEBUGAR O 500 INTERNO.
    """
    form = ProductForm()
    
    # 1. Tenta validar o formulário no submit
    if form.validate_on_submit():
        try:
            file = form.photo.data
            filename = None
            
            # --- Lógica de Upload de Arquivo ---
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                
                # Constrói o caminho de upload
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', str(current_user.id))
                
                # Cria o diretório se ele não existir, exist_ok=True para evitar erros se já existir
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder, exist_ok=True) 
                    
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
            # --- Fim Lógica de Upload ---
            
            # Cria um novo produto com os dados do formulário
            new_product = Product(
                name=form.name.data,
                description=form.description.data,
                price=form.price.data,
                category=form.category.data,
                is_delivery=form.is_delivery.data,
                is_balcao=form.is_balcao.data,
                user_id=current_user.id,
                # Garante que 'filename' está definido (do bloco acima) ou é None
                photo_url=url_for('static', filename=f'uploads/{current_user.id}/{filename}') if filename else None
            )
            
            # --- Lógica de Banco de Dados ---
            db.session.add(new_product)
            db.session.commit()
            
            flash('Produto adicionado com sucesso!', 'success')
            return redirect(url_for('produtos.index'))
            
        except Exception as e:
            # Captura qualquer erro, faz rollback no DB e loga para você ver no console
            db.session.rollback()
            print(f"ERRO CRÍTICO AO ADICIONAR PRODUTO (/produtos/adicionar): {e}")
            
            # Informa o usuário (em vez de mostrar um 500 genérico)
            flash(f'Erro interno ao adicionar produto. Verifique o console para detalhes.', 'danger')
            # Retorna o formulário preenchido para nova tentativa
            return render_template('produtos/adicionar.html', form=form)
            
    # Se for GET ou a validação inicial do formulário falhar (sem exceção)
    return render_template('produtos/adicionar.html', form=form)

@produtos_bp.route('/editar/<int:product_id>', methods=['GET', 'POST'])
@login_required
def editar(product_id):
    """
    Rota para editar um produto existente.
    """
    product = Product.query.filter_by(id=product_id, user_id=current_user.id).first_or_404()
    form = ProductForm(obj=product)

    if form.validate_on_submit(): # Usando validate_on_submit para melhor tratamento de POST
        try:
            # Atualiza os dados do produto com base no formulário
            form.populate_obj(product) # Isso atualiza todos os campos exceto o arquivo, que é manual

            file = request.files.get('photo')
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', str(current_user.id))
                
                # Garante que o diretório existe
                os.makedirs(upload_folder, exist_ok=True)
                
                # Remove a foto antiga se houver
                if product.photo_url:
                    old_filename = os.path.basename(product.photo_url)
                    old_file_path = os.path.join(upload_folder, old_filename)
                    if os.path.exists(old_file_path):
                        os.remove(old_file_path)

                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
                product.photo_url = url_for('static', filename=f'uploads/{current_user.id}/{filename}')
            elif file and file.filename != '':
                flash('Tipo de arquivo não permitido.', 'danger')
                return redirect(url_for('produtos.editar', product_id=product_id))

            db.session.commit()
            flash('Produto atualizado com sucesso!', 'success')
            return redirect(url_for('produtos.index'))
        except Exception as e:
            db.session.rollback()
            print(f"ERRO CRÍTICO AO EDITAR PRODUTO: {e}")
            flash(f'Erro interno ao atualizar produto. Verifique o console para detalhes.', 'danger')
    
    return render_template('produtos/editar.html', form=form, product=product)


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
            try:
                os.remove(file_path)
            except Exception as e:
                # Loga o erro, mas não impede a exclusão do registro no DB
                print(f"ATENÇÃO: Não foi possível remover o arquivo {file_path}. Erro: {e}")

    db.session.delete(product)
    db.session.commit()
    flash('Produto excluído com sucesso!', 'success')
    return redirect(url_for('produtos.index'))
