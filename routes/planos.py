from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import Plan, Subscription, db
from datetime import datetime, timedelta

planos = Blueprint('planos', __name__)

@planos.route('/planos')
@login_required
def choose_plan():
    if current_user.has_active_plan():
        # Se o usuário já tiver um plano ativo, redireciona para o dashboard
        flash('Você já possui um plano ativo.', 'info')
        return redirect(url_for('dashboard.index'))

    # Carrega todos os planos disponíveis do banco de dados
    plans = Plan.query.all()
    return render_template('planos.html', plans=plans)

@planos.route('/planos/selecionar/<int:plan_id>', methods=['POST'])
@login_required
def select_plan(plan_id):
    plan = Plan.query.get_or_404(plan_id)

    # Verifica se já existe uma assinatura para o usuário e plano
    existing_subscription = Subscription.query.filter_by(user_id=current_user.id, plan_id=plan.id).first()

    if plan.name == 'Plano Gratuito': # Opção de plano gratuito
        if existing_subscription and existing_subscription.status != 'canceled':
            flash('Você já ativou seu plano gratuito.', 'warning')
            return redirect(url_for('dashboard.index'))
        
        # Cria e ativa a assinatura de teste
        new_subscription = Subscription(
            user_id=current_user.id,
            plan_id=plan.id,
            status='active',
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=plan.duration_days)
        )
        db.session.add(new_subscription)
        db.session.commit()
        flash('Plano Gratuito ativado com sucesso! Aproveite seus 15 dias de teste.', 'success')
        return redirect(url_for('dashboard.index'))
        
    else: # Opção de plano premium
        # Redireciona para a URL de checkout da Kirvano
        if not plan.kirvano_checkout_url:
            flash('URL de checkout do plano não configurada. Tente outro plano.', 'error')
            return redirect(url_for('planos.choose_plan'))
            
        return redirect(plan.kirvano_checkout_url)

@planos.route('/kirvano_webhook', methods=['POST'])
def kirvano_webhook():
    # Esta rota é para ser usada como um webhook para Kirvano,
    # para receber confirmações de pagamento. A implementação real
    # precisaria de validação de assinatura e lógica de negócio.
    # Exemplo:
    # data = request.json
    # transaction_id = data.get('id_transacao')
    # status = data.get('status')
    
    # if status == 'aprovado':
    #     subscription = Subscription.query.filter_by(kirvano_transaction_id=transaction_id).first()
    #     if subscription:
    #         subscription.set_active(subscription.plan.duration_days)
    #         db.session.commit()
    #         # Opcionalmente, notificar o usuário
    
    return "OK", 200
