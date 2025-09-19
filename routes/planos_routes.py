import os
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from models import db, Plan, User, Subscription
from datetime import datetime, timedelta
import logging

planos_bp = Blueprint('planos', __name__)
logging.basicConfig(level=logging.INFO)

@planos_bp.route('/choose')
@login_required
def choose_plan():
    """Rota para o usuário escolher um plano de assinatura."""
    
    # Verifica se o usuário tem alguma assinatura ativa.
    active_subscription = Subscription.query.filter_by(user_id=current_user.id, status='active').first()
    
    # Verifica se o plano freemium já foi usado (está expirado ou cancelado).
    freemium_used = Subscription.query.filter(
        Subscription.user_id == current_user.id,
        db.exists().where(Plan.id == Subscription.plan_id).where(Plan.name == 'Freemium')
    ).first()
    
    # Carrega os planos Fremium e Premium.
    plans = Plan.query.filter(Plan.name.in_(['Freemium', 'Plano Premium'])).order_by(Plan.price.asc()).all()
    
    # Se o plano freemium já foi usado, remove-o da lista para que não seja exibido novamente.
    if freemium_used and freemium_used.status != 'active':
        plans = [p for p in plans if p.name != 'Freemium']
    
    # Se o usuário já tem um plano pago ativo, redireciona para o dashboard.
    if active_subscription and active_subscription.plan.name != 'Freemium':
        return redirect(url_for('dashboard.index'))
    
    return render_template('planos/choose.html', plans=plans, active_subscription=active_subscription)

@planos_bp.route('/checkout/<int:plan_id>')
@login_required
def checkout(plan_id):
    """
    Rota para iniciar o checkout de um plano de assinatura.
    Redireciona para o link de checkout da Kirvano ou ativa o plano Freemium.
    """
    plan = Plan.query.get_or_404(plan_id)
    
    # Verifica se o usuário já tem um plano ativo.
    existing_subscription = Subscription.query.filter_by(user_id=current_user.id, status='active').first()
    if existing_subscription:
        flash(f'Você já tem uma assinatura ativa ({existing_subscription.plan.name}).', 'info')
        return redirect(url_for('planos.choose_plan'))
    
    if plan.name == 'Freemium':
        # Verifica se o usuário já usou o plano Freemium alguma vez.
        freemium_history = Subscription.query.filter_by(user_id=current_user.id, plan_id=plan.id).first()
        if freemium_history:
            flash('Você já usou seu período de teste do plano Freemium. Por favor, assine o plano Premium para continuar.', 'warning')
            return redirect(url_for('planos.choose_plan'))
        
        # Cria e ativa a assinatura do plano Freemium.
        new_subscription = Subscription(
            user_id=current_user.id,
            plan_id=plan.id,
            status='active',
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=plan.duration_days)
        )
        db.session.add(new_subscription)
        db.session.commit()
        
        flash('Plano Freemium ativado com sucesso!', 'success')
        return redirect(url_for('dashboard.index'))

    if not plan.kirvano_checkout_url:
        flash('O plano selecionado não tem um link de checkout Kirvano configurado.', 'danger')
        return redirect(url_for('planos.choose_plan'))
    
    # Adiciona parâmetros de rastreamento e dados do cliente ao URL da Kirvano.
    kirvano_url = f"{plan.kirvano_checkout_url}?customer_email={current_user.email}&user_id={current_user.id}"
    return redirect(kirvano_url)

@planos_bp.route('/cancel')
@login_required
def cancel_plan():
    """
    Rota para o usuário cancelar sua assinatura.
    """
    # Lógica de cancelamento (a ser implementada).
    pass
