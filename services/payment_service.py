import json
import logging
from datetime import datetime, timedelta
from flask import current_app
from extensions import db
from models import Plan, Subscription, User

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def handle_kirvano_webhook(payload):
    """
    Função para tratar as notificações de webhook da Kirvano.
    Processa eventos de pagamento aprovado para ativar a assinatura do usuário.
    """
    try:
        data = payload.get('data')
        event_type = payload.get('event_type')

        if not data or not event_type:
            logging.warning("Payload do webhook inválido: 'data' ou 'event_type' ausente.")
            return False

        if event_type == 'PURCHASE_APPROVED':
            product_id = data.get('product_id')
            kirvano_transaction_id = data.get('id')
            kirvano_subscription_id = data.get('subscription_id')
            customer = data.get('customer', {})
            email = customer.get('email')
            
            # Use o 'source' para encontrar o user_id que passamos no checkout
            user_id = data.get('source', {}).get('user_id')

            if not all([product_id, kirvano_transaction_id, email, user_id]):
                logging.error(f"Webhook de pagamento aprovado inválido. Dados ausentes: {payload}")
                return False

            # Busca o plano associado ao product_id da Kirvano
            # Note: A lógica para mapear product_id da Kirvano para plan_id local
            # precisa ser implementada. Por enquanto, estamos usando o plano de 30 dias.
            # Em uma implementação completa, você teria um campo 'kirvano_product_id' no modelo Plan.
            plan = Plan.query.filter_by(duration_days=30).first()
            user = User.query.get(user_id)

            if not user or not plan:
                logging.error(f"Usuário ou plano não encontrado. user_id: {user_id}, plan_id (mapeado): {plan.id}")
                return False

            # Desativa qualquer assinatura antiga e cria a nova
            old_subscriptions = Subscription.query.filter_by(user_id=user.id, status='active').all()
            for sub in old_subscriptions:
                sub.status = 'expired'

            new_subscription = Subscription(
                user_id=user.id,
                plan_id=plan.id,
                status='active',
                kirvano_transaction_id=kirvano_transaction_id,
                kirvano_subscription_id=kirvano_subscription_id,
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=plan.duration_days)
            )

            db.session.add(new_subscription)
            db.session.commit()
            logging.info(f"Assinatura do usuário {user_id} ativada com sucesso. Transação Kirvano ID: {kirvano_transaction_id}")
            return True
            
        else:
            logging.info(f"Evento de webhook '{event_type}' recebido, mas não processado.")
            return True # Retorna True para evitar que a Kirvano reenvie o evento

    except Exception as e:
        db.session.rollback()
        logging.error(f"Erro ao processar webhook da Kirvano: {e}", exc_info=True)
        return False
