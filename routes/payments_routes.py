import os
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from extensions import db
from models import User, Plan, Subscription
import logging
from typing import Optional, Dict, Any, Tuple

# Configura o logger para mensagens de erro
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

payments_bp = Blueprint('payments', __name__, url_prefix='/webhooks/payments')

@payments_bp.route('/kirvano', methods=['POST'])
def kirvano_webhook() -> Tuple[jsonify, int]:
    """
    Recebe e processa webhooks da Kirvano para atualizações de pagamentos.
    Este endpoint verifica a autenticidade da requisição e atualiza o status
    da assinatura do usuário no banco de dados.
    """
    # Verifica o cabeçalho X-Kirvano-Token
    kirvano_token = os.getenv('KIRVANO_WEBHOOK_SECRET')
    if request.headers.get('X-Kirvano-Token') != kirvano_token:
        logging.warning("Tentativa de acesso não autorizado ao webhook.")
        return jsonify({'status': 'error', 'message': 'Acesso não autorizado'}), 401

    try:
        payload: Dict[str, Any] = request.json
        event_type: str = payload.get('event_type', '')

        if not event_type:
            logging.warning("Webhook sem tipo de evento. Payload: %s", payload)
            return jsonify({'status': 'error', 'message': 'Tipo de evento ausente'}), 400

        # Mapeia o user_id que passamos no checkout como 'source_id'
        user_id = payload.get('source', {}).get('user_id')
        
        if not user_id:
            logging.error("ID do usuário ausente no payload do webhook. Payload: %s", payload)
            return jsonify({'status': 'error', 'message': 'ID do usuário ausente'}), 400

        user = User.query.get(int(user_id))
        
        if not user:
            logging.error("Usuário com ID %s não encontrado no banco de dados.", user_id)
            return jsonify({'status': 'error', 'message': 'Usuário não encontrado'}), 404
        
        # Lógica para diferentes eventos de webhook
        if event_type == 'COMPRA_APROVADA':
            # Use o kirvano_checkout_url para encontrar o plano correto
            kirvano_checkout_url = payload.get('order', {}).get('products', [{}])[0].get('kirvano_checkout_url')
            if not kirvano_checkout_url:
                logging.error("URL de checkout ausente no webhook de compra aprovada.")
                return jsonify({'status': 'error', 'message': 'URL de checkout ausente'}), 400

            plan = Plan.query.filter_by(kirvano_checkout_url=kirvano_checkout_url).first()
            if not plan:
                logging.error("Plano não encontrado para a URL de checkout: %s", kirvano_checkout_url)
                return jsonify({'status': 'error', 'message': 'Plano não encontrado'}), 404

            # Desativa assinaturas antigas
            Subscription.query.filter_by(user_id=user.id, status='active').update({Subscription.status: 'expired'})

            # Cria a nova assinatura
            new_subscription = Subscription(
                user_id=user.id,
                plan_id=plan.id,
                status='active',
                kirvano_transaction_id=payload.get('id'),
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=plan.duration_days)
            )
            db.session.add(new_subscription)
            db.session.commit()
            logging.info(f"Assinatura ativada para o usuário {user.email}.")
            
        elif event_type == 'COMPRA_RECORRENTE_CANCELADA':
            subscription = Subscription.query.filter_by(user_id=user.id, status='active').first()
            if subscription:
                subscription.status = 'canceled'
                db.session.commit()
                logging.info(f"Assinatura cancelada para o usuário {user.email}.")

        elif event_type == 'COMPRA_RECORRENTE_RENOVADA':
            subscription = Subscription.query.filter_by(user_id=user.id, status='active').first()
            if subscription:
                subscription.end_date += timedelta(days=subscription.plan.duration_days)
                db.session.commit()
                logging.info(f"Assinatura renovada para o usuário {user.email}.")
        
        return jsonify({'status': 'success', 'message': 'Webhook processado'}), 200

    except Exception as e:
        db.session.rollback()
        logging.error("Erro ao processar o webhook: %s", e, exc_info=True)
        return jsonify({'status': 'error', 'message': 'Erro interno no servidor'}), 500
