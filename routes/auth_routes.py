from flask import Blueprint, render_template, redirect, url_for, flash, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import User
from forms import LoginForm, RegisterForm
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import logging

auth_bp = Blueprint('auth', __name__)
logging.basicConfig(level=logging.INFO)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        try:
            # Criação do novo usuário
            hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
            new_user = User(
                name=form.name.data,
                email=form.email.data,
                password_hash=hashed_password,
                phone=form.phone.data,
                created_at=datetime.utcnow()
            )
            db.session.add(new_user)
            db.session.commit()
            
            # As etapas de criação de Restaurante e Assinatura foram removidas daqui
            # A criação do Restaurante deve ser feita após a escolha do plano
            
            flash('Cadastro realizado com sucesso! Escolha um plano para continuar.', 'success')
            logging.info(f"User {new_user.email} registered successfully.")
            
            # Login automático após o cadastro
            login_user(new_user)
            # Redirecionamento para a página de escolha de planos
            return redirect(url_for('planos.choose_plan'))
            
        except IntegrityError:
            db.session.rollback()
            flash('Este e-mail já está cadastrado. Por favor, use outro e-mail.', 'danger')
            logging.error(f"Registration failed for email {form.email.data} due to IntegrityError.")
        except Exception as e:
            db.session.rollback()
            flash(f'Ocorreu um erro inesperado. Tente novamente mais tarde. Erro: {e}', 'danger')
            logging.error(f"Registration failed for email {form.email.data}. Error: {e}")
            
    return render_template('auth/register.html', form=form)
