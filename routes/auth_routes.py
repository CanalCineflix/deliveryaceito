from flask import Blueprint, render_template, redirect, url_for, flash, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import User, Subscription, Plan
from forms import LoginForm, RegisterForm, ChangePasswordForm, RequestPasswordResetForm, ResetPasswordForm
from sqlalchemy.exc import IntegrityError
import logging

auth_bp = Blueprint('auth', __name__)
logging.basicConfig(level=logging.INFO)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        new_user = User(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            restaurant_name=form.restaurant_name.data
        )
        new_user.set_password(form.password.data)
        
        db.session.add(new_user)
        try:
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
            
    return render_template('register.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash('E-mail ou senha incorretos.', 'danger')
    return render_template('login.html', form=form)

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
        if current_user.check_password(form.old_password.data):
            current_user.set_password(form.new_password.data)
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
