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
    Se o usuário já tiver uma assinatura ativa e não for Freemium expirado, o redireciona.
    """
    # 1. Busca todos os planos
    all_plans = Plan.query.all()
    
    # 2. Verifica se o usuário tem uma assinatura ativa, buscando a primeira
    user_subscription = current_user.subscriptions.filter_by(status='active').first()
    
    # Se o usuário já tiver um plano ativo (que não seja Freemium)
    if user_subscription and not user_subscription.plan.is_free:
        return redirect(url_for('planos.my_plan'))

    # 3. Lógica para determinar quais planos exibir
    freemium_plan = Plan.query.filter_by(is_free=True).first()
    premium_plan = Plan.query.filter_by(is_free=False).first()
    
    plans_to_display = []
    
    # Adiciona o plano Premium sempre
    if premium_plan:
        plans_to_display.append(premium_plan)
        
    # Verifica se o Freemium já foi assinado.
    # Se a assinatura freemium existe (ativa, expirada ou cancelada), não exibe a opção novamente.
    freemium_subscription_exists = Subscription.query.filter_by(
        user_id=current_user.id, 
        plan_id=freemium_plan.id
    ).first()
    
    if freemium_plan and not freemium_subscription_exists:
        plans_to_display.append(freemium_plan)

    return render_template('planos/choose.html', plans=plans_to_display)

@planos_bp.route('/subscribe_freemium', methods=['POST'])
@login_required
def subscribe_freemium():
    """
    Processa a assinatura do plano Freemium.
    """
    freemium_plan = Plan.query.filter_by(is_free=True).first()
    if not freemium_plan:
        flash('Plano gratuito não encontrado.', 'danger')
        return redirect(url_for('planos.choose'))

    # Impede que o usuário assine o Freemium mais de uma vez.
    if Subscription.query.filter_by(user_id=current_user.id, plan_id=freemium_plan.id).first():
        flash('Você já utilizou o seu período gratuito. Por favor, escolha um plano pago.', 'warning')
        return redirect(url_for('planos.choose'))

    # Cria a nova assinatura
    new_subscription = Subscription(
        user_id=current_user.id,
        plan_id=freemium_plan.id,
        status='active',
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=freemium_plan.duration_days)
    )
    db.session.add(new_subscription)
    db.session.commit()
    
    flash('Seu plano gratuito foi ativado! Aproveite os 15 dias.', 'success')
    return redirect(url_for('dashboard.home'))

@planos_bp.route('/my')
@login_required
def my_plan():
    """
    Exibe o plano de assinatura atual do usuário logado.
    """
    user_subscription = Subscription.query.filter_by(user_id=current_user.id).order_by(db.desc(Subscription.start_date)).first()
    return render_template('planos/my_plan.html', subscription=user_subscription)

@planos_bp.route('/checkout/<int:plan_id>')
@login_required
def checkout(plan_id):
    """
    Redireciona o usuário para a página de checkout da Kirvano.
    """
    plan = Plan.query.get_or_404(plan_id)
    
    if plan.is_free:
        # Se por algum motivo o checkout for chamado com o plano freemium
        return redirect(url_for('planos.subscribe_freemium'))

    kirvano_checkout_url = plan.kirvano_checkout_url
    
    if not kirvano_checkout_url:
        flash('O plano selecionado não tem um link de checkout Kirvano configurado.', 'danger')
        return redirect(url_for('planos.choose'))

    # Adiciona o email do usuário na URL de checkout para preenchimento automático
    redirect_url = f"{kirvano_checkout_url}?customer_email={current_user.email}&user_id={current_user.id}"
    
    return redirect(redirect_url)

@planos_bp.route('/payment-feedback')
def payment_feedback():
    """
    Exibe uma mensagem ao usuário após o pagamento.
    """
    status = request.args.get('status')
    
    if status == 'approved':
        flash('Pagamento aprovado! Sua assinatura será ativada em breve.', 'success')
    elif status == 'pending':
        flash('Seu pagamento está pendente. A ativação ocorrerá em breve.', 'info')
    else:
        flash('O pagamento falhou. Por favor, tente novamente.', 'danger')
        
    return redirect(url_for('planos.my_plan'))
