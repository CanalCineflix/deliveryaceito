import os
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
from forms import RegistrationForm, LoginForm # Assumindo a existência dessas classes
import logging

auth_bp = Blueprint('auth', __name__)

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Rota para registro de novos usuários. Redireciona para a página de planos após o sucesso."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Gera o hash da senha
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        
        # Cria a instância do usuário
        new_user = User(
            name=form.name.data,
            email=form.email.data,
            password_hash=hashed_password,
            phone=form.phone.data,
            restaurant_name=form.restaurant_name.data,
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            
            # Loga o novo usuário automaticamente
            login_user(new_user)
            flash('Sua conta foi criada com sucesso! Por favor, escolha um plano para continuar.', 'success')
            
            # Redireciona para a página de seleção de planos
            return redirect(url_for('planos.choose_plan'))
            
        except IntegrityError:
            db.session.rollback()
            flash('Este e-mail já está cadastrado. Tente outro ou faça login.', 'danger')
            return redirect(url_for('auth.register'))
            
    return render_template('auth/register.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Rota para login de usuários existentes. Redireciona para a página de planos."""
    if current_user.is_authenticated and current_user.has_active_plan():
        return redirect(url_for('dashboard.index'))
    elif current_user.is_authenticated and not current_user.has_active_plan():
        return redirect(url_for('planos.choose_plan'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            flash(f'Bem-vindo de volta, {user.name}!', 'success')
            
            # Redireciona para a página de seleção de planos, pois o plano pode ter expirado.
            return redirect(url_for('planos.choose_plan'))
        else:
            flash('Login ou senha inválidos. Por favor, tente novamente.', 'danger')
            
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """Rota para desconectar o usuário."""
    logout_user()
    flash('Você foi desconectado com sucesso.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    """A ser implementado."""
    flash('Funcionalidade de recuperação de senha em desenvolvimento.', 'info')
    return redirect(url_for('auth.login'))
