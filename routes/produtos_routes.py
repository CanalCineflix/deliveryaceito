import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models import db, Product # Assumindo que o modelo Product está no arquivo models.py
# Importamos FileStorage para checagem de tipo em uploads, garantindo que um arquivo foi submetido.
from werkzeug.datastructures import FileStorage 
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
    # Filtra produtos apenas do usuário logado e ordena por nome.
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
        # Captura os dados do formulário com sucesso, agora processa
        try:
            # Pega o objeto FileStorage do campo do formulário
            file = form.photo.data 
            filename = None
            
            # --- Lógica de Upload de Arquivo ---
            # Verifica se o campo não está vazio (ou se é um FileStorage e tem nome de arquivo)
            if file and file.filename and allowed_file(file.filename): 
                filename = secure_filename(file.filename)
                
                # Constrói o caminho de upload: static/uploads/user_id/
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', str(current_user.id))
                
                # Cria o diretório se ele não existir
                os.makedirs(upload_folder, exist_ok=True)  
                    
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
            elif file and file.filename and not allowed_file(file.filename):
                flash('Tipo de arquivo não permitido.', 'danger')
                return redirect(url_for('produtos.adicionar'))
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
                # Define a URL do arquivo no banco de dados
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
            
            # Informa o usuário e redireciona
            flash(f'Erro interno ao adicionar produto. Verifique o console para detalhes.', 'danger')
            return redirect(url_for('produtos.index')) 
            
    # Se for GET ou falha de validação do formulário (exceto file upload que é tratada acima)
    products = Product.query.filter_by(user_id=current_user.id).order_by(Product.name).all()
    # Assume que o formulário de adição é um modal ou está na mesma página de listagem
    return render_template('perfil/products.html', products=products, form=form)


@produtos_bp.route('/editar/<int:product_id>', methods=['GET', 'POST'])
@login_required
def editar(product_id):
    """
    Rota para editar um produto existente.
    """
    # Garante que apenas o usuário proprietário possa editar o produto
    product = Product.query.filter_by(id=product_id, user_id=current_user.id).first_or_404()
    form = ProductForm(obj=product)

    if form.validate_on_submit():
        try:
            # 1. Atualiza os campos de texto/número do produto
            # form.populate_obj(product) deve vir antes do commit
            form.populate_obj(product) 

            # 2. Lógica de Upload de Nova Foto (Substituição)
            # CORREÇÃO: Usando form.photo.data para consistência com Flask-WTF
            new_file = form.photo.data
            
            # Checa se um novo arquivo foi fornecido
            if new_file and new_file.filename and new_file.filename != '':
                
                if allowed_file(new_file.filename):
                    filename = secure_filename(new_file.filename)
                    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', str(current_user.id))
                    
                    os.makedirs(upload_folder, exist_ok=True)
                    
                    # Remove a foto antiga se houver e a URL existir
                    if product.photo_url:
                        # Extrai o nome do arquivo da URL para reconstruir o caminho no servidor
                        old_filename = os.path.basename(product.photo_url)
                        old_file_path = os.path.join(upload_folder, old_filename)
                        
                        if os.path.exists(old_file_path):
                            try:
                                os.remove(old_file_path)
                            except Exception as e:
                                print(f"ATENÇÃO: Não foi possível remover o arquivo antigo {old_file_path}. Erro: {e}")

                    # Salva o novo arquivo
                    file_path = os.path.join(upload_folder, filename)
                    new_file.save(file_path)
                    
                    # Atualiza o URL do produto no objeto
                    product.photo_url = url_for('static', filename=f'uploads/{current_user.id}/{filename}')
                else:
                    flash('Tipo de arquivo não permitido.', 'danger')
                    # Retorna para o template de listagem/edição para mostrar o erro
                    products = Product.query.filter_by(user_id=current_user.id).order_by(Product.name).all()
                    return render_template('perfil/products.html', products=products, form=form, product=product, editing=True)

            # 3. Comita as alterações no banco de dados (incluindo a nova photo_url, se houver)
            db.session.commit()
            flash('Produto atualizado com sucesso!', 'success')
            return redirect(url_for('produtos.index'))
            
        except Exception as e:
            db.session.rollback()
            print(f"ERRO CRÍTICO AO EDITAR PRODUTO: {e}")
            flash(f'Erro interno ao atualizar produto. Verifique o console para detalhes.', 'danger')
            return redirect(url_for('produtos.index')) 

    # Se for GET, pré-preenche o formulário e renderiza 
    products = Product.query.filter_by(user_id=current_user.id).order_by(Product.name).all()
    # 'editing=True' pode ser usado no template para abrir o modal de edição automaticamente
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
    """
    product = Product.query.filter_by(id=product_id, user_id=current_user.id).first_or_404()
    
    # Remove a foto do servidor se ela existir
    if product.photo_url:
        # Reconstroi o caminho no sistema de arquivos a partir da URL
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
