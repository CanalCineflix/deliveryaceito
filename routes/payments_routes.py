import os
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from extensions import db
from models import User, Plan, Subscription
import logging
from typing import Optional, Dict, Any, Tuple

# Configura o logger para mensagens de erro
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

payments_bp = Blueprint('payments', __name__)

# Configura a chave de API (idealmente de uma variável de ambiente)
# O tipo Optional[str] indica que a variável pode ser uma string ou None
KIRVANO_API_KEY: Optional[str] = os.getenv('KIRVANO_WEBHOOK_SECRET')

# Verificação crucial: garante que a chave de API foi definida no ambiente
if not KIRVANO_API_KEY:
    logging.error("A variável de ambiente 'KIRVANO_WEBHOOK_SECRET' não está configurada.")
    # Dependendo da sua necessidade, você pode levantar uma exceção aqui
    # para evitar que a aplicação inicie sem a chave de segurança.

@payments_bp.route('/kirvano', methods=['POST'])
def kirvano_webhook() -> Tuple[jsonify, int]:
    """
    Recebe e processa webhooks da Kirvano para atualizações de pagamentos.
    Este endpoint verifica a autenticidade da requisição e atualiza o status
    da assinatura do usuário no banco de dados.
    """
    try:
        # 1. Verificação da Chave de Segurança (API Key)
        # O token deve ser enviado no cabeçalho da requisição como 'X-Kirvano-Token'
        token_recebido: Optional[str] = request.headers.get('X-Kirvano-Token')
        
        # A verificação agora inclui a garantia de que nossa própria chave não é None
        if not token_recebido or token_recebido != KIRVANO_API_KEY:
            logging.warning("Tentativa de acesso não autorizado ao webhook. Token recebido: %s", token_recebido)
            return jsonify({"status": "error", "message": "Acesso não autorizado"}), 401

        data: Dict[str, Any] = request.json
        event_type: Optional[str] = data.get('event')
        
        if event_type == 'paid':
            # Obtém os dados relevantes do payload do webhook
            product_id: Optional[str] = data.get('product', {}).get('id')
            user_id: Optional[str] = data.get('external_id') # Assume que você passou o user_id no checkout como external_id

            logging.info("Webhook 'paid' recebido. product_id: %s, user_id: %s", product_id, user_id)

            # 2. Identificador de Usuário e Produto
            # Garante que user_id e product_id não são None antes de usá-los na query
            if not user_id or not product_id:
                logging.error("Dados de usuário ou produto ausentes no webhook.")
                return jsonify({"status": "error", "message": "Dados do webhook ausentes"}), 400

            user: Optional[User] = User.query.get(user_id)
            plan: Optional[Plan] = Plan.query.filter_by(kirvano_product_id=product_id).first()

            if not user:
                logging.error("Usuário não encontrado para o ID: %s", user_id)
                return jsonify({"status": "error", "message": "Usuário não encontrado"}), 404
            
            if not plan:
                logging.error("Plano não encontrado para o product_id da Kirvano: %s", product_id)
                return jsonify({"status": "error", "message": "Plano não encontrado"}), 404

            # Desativa qualquer assinatura ativa existente do usuário
            active_subscription: Optional[Subscription] = Subscription.query.filter_by(user_id=user.id, status='active').first()
            if active_subscription:
                active_subscription.status = 'inactive'
                db.session.add(active_subscription)

            # Cria uma nova assinatura ativa para o usuário
            nova_assinatura: Subscription = Subscription(
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
        logging.error(f"Erro ao processar o webhook: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Erro interno no servidor"}), 500
