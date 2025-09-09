import os
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from extensions import db
from models import User, Plan, Subscription
import logging

# Configura o logger para mensagens de erro
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

payments_bp = Blueprint('payments', __name__)

# Configura a chave de API (idealmente de uma variável de ambiente)
KIRVANO_API_KEY = os.getenv('KIRVANO_WEBHOOK_SECRET')

@payments_bp.route('/kirvano', methods=['POST'])
def kirvano_webhook():
    """
    Recebe e processa webhooks da Kirvano para atualizações de pagamentos.
    Este endpoint verifica a autenticidade da requisição e atualiza o status
    da assinatura do usuário no banco de dados.
    """
    try:
        # 1. Verificação da Chave de Segurança (API Key)
        # O token deve ser enviado no cabeçalho da requisição como 'X-Kirvano-Token'
        token_recebido = request.headers.get('X-Kirvano-Token')
        
        if not token_recebido or token_recebido != KIRVANO_API_KEY:
            logging.warning("Tentativa de acesso não autorizado ao webhook. Token recebido: %s", token_recebido)
            return jsonify({"status": "error", "message": "Acesso não autorizado"}), 401

        data = request.json
        event_type = data.get('event')
        
        if event_type == 'paid':
            # Obtém os dados relevantes do payload do webhook
            product_id = data.get('product', {}).get('id')
            user_id = data.get('external_id') # Assume que você passou o user_id no checkout como external_id

            logging.info("Webhook 'paid' recebido. product_id: %s, user_id: %s", product_id, user_id)

            # 2. Identificador de Usuário e Produto
            user = User.query.get(user_id)
            plan = Plan.query.filter_by(kirvano_product_id=product_id).first()

            if not user:
                logging.error("Usuário não encontrado para o ID: %s", user_id)
                return jsonify({"status": "error", "message": "Usuário não encontrado"}), 404
            
            if not plan:
                logging.error("Plano não encontrado para o product_id da Kirvano: %s", product_id)
                return jsonify({"status": "error", "message": "Plano não encontrado"}), 404

            # Desativa qualquer assinatura ativa existente do usuário
            active_subscription = Subscription.query.filter_by(user_id=user.id, status='active').first()
            if active_subscription:
                active_subscription.status = 'inactive'
                db.session.add(active_subscription)

            # Cria uma nova assinatura ativa para o usuário
            nova_assinatura = Subscription(
                user_id=user.id,
                plan_id=plan.id,
                status='active',
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=plan.duration_days)
            )
            db.session.add(nova_assinatura)

            # 3. Transações e Rollbacks
            db.session.commit()
            logging.info("Assinatura do usuário %s atualizada para o plano %s.", user_id, plan.name)

            return jsonify({"status": "success", "message": "Webhook processado com sucesso"}), 200
        
        else:
            # Outros tipos de eventos podem ser tratados aqui (reembolso, estorno, etc.)
            return jsonify({"status": "info", "message": f"Tipo de evento '{event_type}' ignorado"}), 200

    except Exception as e:
        # 3. Transações e Rollbacks
        db.session.rollback()
        logging.error("Erro ao processar o webhook: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": "Erro interno no servidor"}), 500
