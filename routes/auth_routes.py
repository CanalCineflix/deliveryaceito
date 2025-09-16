import os
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Plan, Subscription
from forms import RegistrationForm, LoginForm
import uuid
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
from datetime import date
from flask import Flask, redirect, url_for, flash
import requests
import json
import logging

auth_bp = Blueprint('auth', __name__)

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# URL da API de integração Kirvano
KIRVANO_API_URL = "https://integrations.kirvano.com/v1"

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        
        # Gera o hash da senha
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        
        # Cria a instância do usuário, incluindo o telefone e o nome do restaurante
        new_user = User(
            name=form.name.data,
            email=form.email.data,
            password_hash=hashed_password,
            phone=form.phone.data,
            restaurant_name=form.restaurant_name.data,
            created_at=datetime.utcnow()
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            
            # --- Lógica adicionada para o plano Freemium ---
            freemium_plan = Plan.query.filter_by(name='Freemium').first()
            if freemium_plan:
                new_subscription = Subscription(
                    user_id=new_user.id,
                    plan_id=freemium_plan.id,
                    status='active',
                    start_date=datetime.utcnow(),
                    end_date=datetime.utcnow() + timedelta(days=freemium_plan.duration_days)
                )
                db.session.add(new_subscription)
                db.session.commit()
                logging.info(f'Plano Freemium atribuído ao usuário {new_user.email}.')
                flash('Cadastro realizado com sucesso! Seu plano de 15 dias já está ativo. Bem-vindo(a)!', 'success')
                login_user(new_user)
                return redirect(url_for('dashboard.index'))
            else:
                flash('Erro ao atribuir o plano inicial. Por favor, entre em contato com o suporte.', 'danger')
                return redirect(url_for('auth.login'))
            # --- Fim da lógica Freemium ---
            
        except IntegrityError:
            db.session.rollback()
            flash('Este e-mail já está cadastrado. Tente outro ou faça login.', 'danger')
            return redirect(url_for('auth.register'))
            
    return render_template('auth/register.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash(f'Bem-vindo de volta, {user.name}!', 'success')
            return redirect(next_page or url_for('dashboard.index'))
        else:
            flash('Login ou senha inválidos. Por favor, tente novamente.', 'danger')
            
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado com sucesso.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    # Lógica a ser implementada para solicitação de redefinição de senha
    flash('Funcionalidade de recuperação de senha em desenvolvimento.', 'info')
    return redirect(url_for('auth.login'))
