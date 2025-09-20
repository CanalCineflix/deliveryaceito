import os
from flask import Blueprint, redirect, url_for, flash
from flask_login import current_user, login_required
from extensions import db
from models import Plan, User
import logging

# Configura o logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# O Blueprint 'payments' agora lida com o checkout do lado do usuário
payments_bp = Blueprint('payments', __name__, url_prefix='/payments')

@payments_bp.route('/checkout/<int:plan_id>')
@login_required
def checkout(plan_id: int):
    """
    Redireciona o usuário para a página de checkout da Kirvano
    com base no ID do plano selecionado.
    """
    logging.info(f"Usuário {current_user.id} solicitou checkout para o plano {plan_id}.")
    
    plan = Plan.query.get(plan_id)
    
    if not plan:
        logging.warning(f"Plano com ID {plan_id} não encontrado.")
        flash('Plano não encontrado.', 'error')
        return redirect(url_for('planos_bp.planos'))
    
    # A URL que você forneceu: https://pay.kirvano.com/7344c061-5d52-49c6-8989-ab73b215687f
    # Você deve salvar este link no campo `kirvano_checkout_url` do seu modelo de dados `Plan`
    # para o Plano Premium.
    
    if not plan.kirvano_checkout_url:
        logging.warning(f"Plano {plan.name} não tem uma URL de checkout configurada.")
        flash('Este plano não tem uma URL de checkout configurada.', 'error')
        return redirect(url_for('planos_bp.planos'))

    # Anexa o ID do usuário ao URL de checkout como um parâmetro de rastreamento.
    # Isso é crucial para que o webhook possa identificar o usuário de volta.
    checkout_url_with_user_id = f"{plan.kirvano_checkout_url}?source_id={current_user.id}"
    
    logging.info(f"Redirecionando usuário {current_user.id} para o checkout: {checkout_url_with_user_id}")
    return redirect(checkout_url_with_user_id)
