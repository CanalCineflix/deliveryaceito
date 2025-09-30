import os # Mantido por precaução, mas não é mais essencial. Será removido no final se não for usado.
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models import db, Product # Assumindo que o modelo Product está no arquivo models.py
# Removidas as importações de FileStorage e secure_filename, pois não estamos lidando com upload de arquivos.
from forms import ProductForm 

# Criação do Blueprint para as rotas de produtos
produtos_bp = Blueprint('produtos', __name__, url_prefix='/produtos')

# REMOVIDO: A função allowed_file não é mais necessária, pois usamos uma URL string.
# def allowed_file(filename):
#     ...

@produtos_bp.route('/')
@login_required
def index():
    """
    Rota principal da gestão de produtos.
    Exibe a lista de todos os produtos do usuário logado.
    """
    # Filtra produtos apenas do usuário logado e ordena por nome.
    products = Product.query.filter_by(user_id=current_user.id).order_by(Product.name).all()
    # Instanciamos o form aqui caso ele seja usado para a adição rápida no mesmo template
    form = ProductForm() 
    return render_template('perfil/products.html', products=products, form=form)

@produtos_bp.route('/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar():
    """
    Rota para adicionar um novo produto.
    Utiliza form.photo_url.data (URL) diretamente.
    """
    form = ProductForm()
    
    if form.validate_on_submit():
        # Lógica de upload de arquivo (FileStorage) removida
        
        try:
            # Cria um novo produto com os dados do formulário
            new_product = Product(
                name=form.name.data,
                description=form.description.data,
                price=form.price.data,
                category=form.category.data,
                is_active=form.is_active.data,
                is_delivery=form.is_delivery.data,
                is_balcao=form.is_balcao.data,
                user_id=current_user.id,
                # CRÍTICO: Usando form.photo_url.data diretamente (string da URL)
                photo_url=form.photo_url.data if form.photo_url.data else None
            )
            
            # --- Lógica de Banco de Dados ---
            db.session.add(new_product)
            db.session.commit()
            
            flash('Produto adicionado com sucesso!', 'success')
            return redirect(url_for('produtos.index'))
            
        except Exception as e:
            # Em caso de erro, desfaz a transação no banco de dados (rollback)
            db.session.rollback()
            print(f"ERRO CRÍTICO AO ADICIONAR PRODUTO (/produtos/adicionar): {e}")
            
            # Informa o usuário e redireciona
            flash(f'Erro interno ao adicionar produto. Verifique o console para detalhes.', 'danger')
            return redirect(url_for('produtos.index'))
            
    # Se for GET ou falha de validação do formulário, renderiza
    products = Product.query.filter_by(user_id=current_user.id).order_by(Product.name).all()
    return render_template('perfil/products.html', products=products, form=form)


@produtos_bp.route('/editar/<int:product_id>', methods=['GET', 'POST'])
@login_required
def editar(product_id):
    """
    Rota para editar um produto existente.
    Garante que o produto pertence ao usuário logado e atualiza o photo_url.
    """
    # Garante que apenas o usuário proprietário possa editar o produto
    product = Product.query.filter_by(id=product_id, user_id=current_user.id).first_or_404()
    # Preenche o formulário com os dados existentes do produto
    form = ProductForm(obj=product)

    if form.validate_on_submit():
        try:
            # CRÍTICO: form.populate_obj(product) atualiza todos os campos, 
            # incluindo o photo_url (string da URL).
            form.populate_obj(product) 

            # A lógica de remoção de arquivo antiga ou upload de nova foto 
            # baseada em FileStorage foi REMOVIDA. 
            # A atualização do URL é feita via form.populate_obj.

            # Comita as alterações no banco de dados
            db.session.commit()
            flash('Produto atualizado com sucesso!', 'success')
            return redirect(url_for('produtos.index'))
            
        except Exception as e:
            db.session.rollback()
            print(f"ERRO CRÍTICO AO EDITAR PRODUTO: {e}")
            flash(f'Erro interno ao atualizar produto. Verifique o console para detalhes.', 'danger')
            return redirect(url_for('produtos.index'))

    # Se for GET ou falha de validação, pré-preenche o formulário e renderiza 
    products = Product.query.filter_by(user_id=current_user.id).order_by(Product.name).all()
    # 'editing=True' sinaliza ao template para abrir o formulário/modal de edição
    return render_template('perfil/products.html', products=products, form=form, product=product, editing=True)


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
    A lógica de remoção de foto do servidor foi REMOVIDA.
    """
    # Garante que o produto pertence ao usuário logado
    product = Product.query.filter_by(id=product_id, user_id=current_user.id).first_or_404()
    
    # REMOVIDO: Lógica de Remoção da Foto do Servidor, pois a foto é externa (URL)
    # if product.photo_url:
    #     upload_folder = os.path.join(...)
    #     ...
    #     if os.path.exists(file_path):
    #         os.remove(file_path)

    # Exclui o produto do banco de dados
    db.session.delete(product)
    db.session.commit()
    flash('Produto excluído com sucesso!', 'success')
    return redirect(url_for('produtos.index'))
