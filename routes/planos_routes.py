import os
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Plan, Subscription, User
from datetime import datetime, timedelta

# Blueprint para rotas de planos
planos_bp = Blueprint('planos', __name__, url_prefix='/planos')

@planos_bp.route('/choose')
@login_required
def choose():
    """
    Exibe a lista de planos de assinatura disponíveis.
    Redireciona para o dashboard se o usuário já tiver um plano ativo.
    """
    if current_user.has_active_plan():
        flash('Seu plano já está ativo! Bem-vindo de volta.', 'info')
        return redirect(url_for('dashboard'))
    
    plans = Plan.query.all()
    # Verifica se o usuário ainda está no período de teste de 15 dias
    is_trial_active = (datetime.utcnow() - current_user.created_at) <= timedelta(days=15)
    
    # Verifica se o usuário já teve uma assinatura paga
    paid_subscription_exists = Subscription.query.filter_by(user_id=current_user.id).first()
    
    return render_template('planos/choose.html', plans=plans, is_trial_active=is_trial_active, paid_subscription_exists=paid_subscription_exists)

@planos_bp.route('/my')
@login_required
def my_plan():
    """
    Exibe o plano de assinatura atual do usuário logado.
    """
    subscription = Subscription.query.filter_by(user_id=current_user.id, status='active').order_by(db.desc(Subscription.end_date)).first()
    
    # Adiciona a lógica para o plano de teste
    if not subscription:
        is_trial_active = (datetime.utcnow() - current_user.created_at) <= timedelta(days=15)
        if is_trial_active:
            # Cria um objeto de assinatura temporário para a visualização
            subscription = Subscription(status='trial', end_date=current_user.created_at + timedelta(days=15))
            subscription.plan = Plan(name='Freemium', price=0.0, description='Período de teste')

    return render_template('planos/my_plan.html', subscription=subscription)

@planos_bp.route('/upgrade')
@login_required
def upgrade():
    """
    Exibe a página de upgrade de plano.
    """
    current_subscription = Subscription.query.filter_by(user_id=current_user.id, status='active').first()
    plans = Plan.query.all()
    return render_template('planos/upgrade.html', current_subscription=current_subscription, plans=plans)

@planos_bp.route('/checkout/<int:plan_id>')
@login_required
def checkout(plan_id):
    """
    Redireciona o usuário para a página de checkout da Kirvano.
    A ativação da assinatura será feita via webhook após o pagamento.
    """
    plan = Plan.query.get_or_404(plan_id)
    
    # A URL do checkout da Kirvano deve ser configurada no seu plano
    kirvano_checkout_url = plan.kirvano_checkout_url
    
    if not kirvano_checkout_url:
        flash('O plano selecionado não tem um link de checkout Kirvano configurado.', 'danger')
        return redirect(url_for('planos.choose'))

    # Adiciona o email do usuário na URL de checkout para preenchimento automático
    # e passa o user_id como um parâmetro de referência. O nome do parâmetro deve ser 'source_id'
    # para ser reconhecido corretamente pelo webhook da Kirvano.
    redirect_url = f"{kirvano_checkout_url}?customer_email={current_user.email}&source_id={current_user.id}"
    
    return redirect(redirect_url)

@planos_bp.route('/payment-feedback')
def payment_feedback():
    """
    Exibe uma mensagem ao usuário após o pagamento, com base nos parâmetros da URL.
    A ativação real da assinatura já foi (ou será) processada pelo webhook.
    """
    status = request.args.get('status')
    
    if status == 'approved':
        flash('Pagamento aprovado! Sua assinatura será ativada em breve.', 'success')
    elif status == 'pending':
        flash('Seu pagamento está pendente. A ativação ocorrerá em breve.', 'info')
    else:
        flash('O pagamento falhou. Por favor, tente novamente.', 'danger')
        
    return redirect(url_for('planos.my_plan'))
