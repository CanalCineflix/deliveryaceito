from models import User, Subscription, Plan
from extensions import db
from datetime import datetime, timedelta
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)

def handle_kirvano_webhook(event_type, payload):
    """
    Lida com os diferentes tipos de eventos de webhook da Kirvano,
    atualizando o estado do usuário e da assinatura no banco de dados.
    """
    try:
        # A Kirvano pode enviar diferentes identificadores no payload.
        # Vamos preferir o user_id que enviamos na URL de checkout,
        # pois é mais direto e seguro.
        user_id = payload.get('customer', {}).get('user_id')
        
        if not user_id:
            logging.error("ID do usuário não encontrado no payload do webhook.")
            return

        user = User.query.get(user_id)

        if not user:
            logging.warning(f"Usuário com ID {user_id} não encontrado no DB.")
            return

        if event_type == 'COMPRA_APROVADA':
            handle_payment_success(user, payload)

        elif event_type == 'COMPRA_RECORRENTE_CANCELADA':
            handle_subscription_canceled(user, payload)

        elif event_type == 'COMPRA_RECORRENTE_RENOVADA':
            handle_subscription_renewed(user, payload)

        # Adicione outros eventos conforme necessário (e.g., COMPRA_ESTORNADA)
        
        db.session.commit()
        logging.info(f"Webhook '{event_type}' processado para o usuário {user.email}.")

    except Exception as e:
        db.session.rollback()
        logging.error(f"Erro ao lidar com o webhook: {e}", exc_info=True)

def handle_payment_success(user, payload):
    """
    Lida com um evento de compra aprovada, ativando a assinatura do usuário.
    """
    order_data = payload.get('order', {})
    product_data = order_data.get('products', [{}])[0]
    
    # Use o kirvano_checkout_url para encontrar o plano correto no DB.
    # É uma forma segura de mapear o produto da Kirvano ao seu plano.
    kirvano_checkout_url = product_data.get('kirvano_checkout_url')
    plan = Plan.query.filter_by(kirvano_checkout_url=kirvano_checkout_url).first()
    
    if not plan:
        logging.error(f"Plano com URL de checkout '{kirvano_checkout_url}' não encontrado no DB.")
        return

    # Procura por uma assinatura existente ativa para o usuário
    subscription = Subscription.query.filter_by(user_id=user.id).first()
    if not subscription:
        subscription = Subscription(user_id=user.id, plan_id=plan.id)
        db.session.add(subscription)
    else:
        # Se existir, apenas atualiza
        subscription.plan_id = plan.id

    # Atualiza os dados da assinatura
    subscription.status = 'active'
    subscription.start_date = datetime.utcnow()
    subscription.end_date = subscription.start_date + timedelta(days=plan.duration_days)
    
    logging.info(f"Assinatura do usuário {user.email} ativada com sucesso.")

def handle_subscription_canceled(user, payload):
    """
    Lida com o cancelamento de uma assinatura recorrente.
    """
    subscription = Subscription.query.filter_by(user_id=user.id).first()
    if subscription:
        subscription.status = 'canceled'
        db.session.commit()
        logging.info(f"Assinatura do usuário {user.email} cancelada.")
    else:
        logging.warning(f"Assinatura não encontrada para o usuário {user.email} para cancelamento.")

def handle_subscription_renewed(user, payload):
    """
    Lida com a renovação automática de uma assinatura recorrente.
    """
    subscription = Subscription.query.filter_by(user_id=user.id).first()
    if subscription and subscription.status == 'active':
        plan = subscription.plan
        if plan:
            # Estende a data de término
            subscription.end_date += timedelta(days=plan.duration_days)
            db.session.commit()
            logging.info(f"Assinatura do usuário {user.email} renovada com sucesso.")
    else:
        logging.warning(f"Assinatura do usuário {user.email} não encontrada ou não está ativa para renovação.")
