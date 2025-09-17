from flask import Blueprint, render_template, redirect, url_for, flash, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import User, Restaurant, Subscription, Plan # Adicionado 'Restaurant' aqui
from forms import LoginForm, RegisterForm, ChangePasswordForm, RequestPasswordResetForm, ResetPasswordForm
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
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
            
            # Criação do restaurante vinculado ao novo usuário
            new_restaurant = Restaurant(
                user_id=new_user.id,
                name=form.restaurant_name.data,
                created_at=datetime.utcnow()
            )
            db.session.add(new_restaurant)
            
            # Criação de uma assinatura vazia para o novo usuário
            trial_plan = Plan.query.filter_by(name="Plano Essencial").first()
            if not trial_plan:
                 trial_plan = Plan(name="Plano Essencial", price=0.00, features="Acesso básico", duration_days=30, is_active=True)
                 db.session.add(trial_plan)
                 db.session.commit()
                 
            new_subscription = Subscription(
                user_id=new_user.id,
                plan_id=trial_plan.id,
                start_date=datetime.utcnow(),
                end_date = datetime.utcnow() + timedelta(days=trial_plan.duration_days),
                is_active=True
            )
            db.session.add(new_subscription)

            db.session.commit()
            
            flash('Cadastro realizado com sucesso! Escolha um plano para continuar.', 'success')
            logging.info(f"User {new_user.email} registered successfully.")
            
            # Login automático após o cadastro
            login_user(new_user)
            return redirect(url_for('plans.choose_plan'))
            
        except IntegrityError:
            db.session.rollback()
            flash('Este e-mail já está cadastrado. Por favor, use outro e-mail.', 'danger')
            logging.error(f"Registration failed for email {form.email.data} due to IntegrityError.")
        except Exception as e:
            db.session.rollback()
            flash('Ocorreu um erro inesperado. Tente novamente mais tarde.', 'danger')
            logging.error(f"Registration failed for email {form.email.data}. Error: {e}")
            
    return render_template('auth/register.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember_me.data)
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash('E-mail ou senha incorretos.', 'danger')
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if check_password_hash(current_user.password_hash, form.old_password.data):
            current_user.password_hash = generate_password_hash(form.new_password.data, method='pbkdf2:sha256')
            db.session.commit()
            flash('Sua senha foi alterada com sucesso!', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash('Senha antiga incorreta.', 'danger')
    return render_template('change_password.html', form=form)

@auth_bp.route('/request_password_reset', methods=['GET', 'POST'])
def request_password_reset():
    form = RequestPasswordResetForm()
    if form.validate_on_submit():
        # Lógica para enviar e-mail de redefinição de senha
        flash('Se o e-mail estiver cadastrado, um link para redefinir a senha será enviado.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('request_password_reset.html', form=form)

@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    # Lógica para verificar o token e redefinir a senha
    form = ResetPasswordForm()
    if form.validate_on_submit():
        flash('Sua senha foi redefinida com sucesso.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('reset_password.html', form=form)
