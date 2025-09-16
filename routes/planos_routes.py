import os
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from models import db, Plan, User, Subscription

planos_bp = Blueprint('planos', __name__)

@planos_bp.route('/choose')
@login_required
def choose_plan():
    """Rota para o usuário escolher um plano de assinatura."""
    plans = Plan.query.order_by(Plan.price.asc()).all()
    # Verifica se o usuário já tem uma assinatura ativa
    # Se sim, redireciona para a página de gerenciamento de assinatura
    active_subscription = Subscription.query.filter_by(user_id=current_user.id, status='active').first()
    if active_subscription:
        return redirect(url_for('dashboard.index'))
    return render_template('planos/choose.html', plans=plans)

@planos_bp.route('/checkout/<int:plan_id>')
@login_required
def checkout(plan_id):
    """
    Rota para iniciar o checkout de um plano de assinatura.
    Redireciona para o link de checkout da Kirvano.
    """
    plan = Plan.query.get_or_404(plan_id)
    
    if not plan.kirvano_checkout_url:
        flash('O plano selecionado não tem um link de checkout Kirvano configurado.', 'danger')
        return redirect(url_for('planos.choose_plan'))
    
    # Adiciona parâmetros de rastreamento e dados do cliente ao URL da Kirvano
    kirvano_url = f"{plan.kirvano_checkout_url}?customer_email={current_user.email}&user_id={current_user.id}"
    
    return redirect(kirvano_url)

@planos_bp.route('/cancel')
@login_required
def cancel_plan():
    """
    Rota para o usuário cancelar sua assinatura.
    """
    # Lógica de cancelamento (a ser implementada)
    pass
