# webhooks_bp.py
import logging
import os
from flask import Blueprint, request, jsonify
from extensions import db
from models import User, Subscription, Plan
from datetime import datetime, timedelta

# Crie um Blueprint para as rotas de webhook
webhooks_bp = Blueprint('webhooks', __name__)
logging.basicConfig(level=logging.INFO)

# Opcional: Pegue o token de segurança da Kirvano das variáveis de ambiente
# kirvano_secret = os.environ.get('KIRVANO_WEBHOOK_SECRET')

@webhooks_bp.route('/kirvano_webhook', methods=['POST'])
def kirvano_webhook():
    """
    Endpoint para receber notificações de webhook da Kirvano.
    Processa o pagamento para ativar a assinatura do plano Premium.
    """
    try:
        # # Opcional: Verificação de segurança para o token do webhook
        # provided_signature = request.headers.get('X-Kirvano-Signature')
        # if not provided_signature or provided_signature != kirvano_secret:
        #     logging.warning("Tentativa de webhook com token inválido.")
        #     return jsonify({"status": "error", "message": "Token inválido"}), 403

        data = request.json
        logging.info(f"Webhook da Kirvano recebido: {data}")

        event_type = data.get('event')
        
        # O que nos interessa é a confirmação de pagamento ou ativação de assinatura.
        if event_type in ['purchase_paid', 'subscription_activated']:
            # Extrair dados da notificação
            transaction_id = data.get('id')
            user_email = data.get('customer', {}).get('email')
            
            if not user_email or not transaction_id:
                logging.warning("Dados essenciais (e-mail ou ID da transação) ausentes no webhook.")
                return jsonify({"status": "error", "message": "Dados ausentes"}), 400

            # 1. Encontre o usuário pelo e-mail
            user = User.query.filter_by(email=user_email).first()
            if not user:
                logging.error(f"Usuário com e-mail {user_email} não encontrado.")
                # Retornar 200 para não reenviar o webhook
                return jsonify({"status": "error", "message": "Usuário não encontrado"}), 200
            
            # 2. Encontre o plano Premium.
            premium_plan = Plan.query.filter(Plan.name == 'Plano Premium').first()

            if not premium_plan:
                logging.error("Plano Premium não encontrado no banco de dados. Configure-o primeiro.")
                return jsonify({"status": "error", "message": "Plano não configurado"}), 500

            # 3. Verifique se a assinatura já existe ou crie uma nova
            subscription = Subscription.query.filter_by(user_id=user.id, plan_id=premium_plan.id).first()
            if subscription:
                # Se a assinatura existe, apenas atualize o status e o ID da transação
                subscription.status = 'active'
                subscription.kirvano_transaction_id = transaction_id
                # Para planos recorrentes, o end_date pode ser atualizado a cada cobrança.
                subscription.end_date = datetime.utcnow() + timedelta(days=premium_plan.duration_days)
            else:
                # Se a assinatura não existe, crie uma nova
                subscription = Subscription(
                    user_id=user.id,
                    plan_id=premium_plan.id,
                    status='active',
                    kirvano_transaction_id=transaction_id,
                    start_date=datetime.utcnow(),
                    end_date=datetime.utcnow() + timedelta(days=premium_plan.duration_days)
                )
                db.session.add(subscription)
            
            db.session.commit()
            logging.info(f"Assinatura do plano Premium ativada para {user_email} com sucesso. Transação: {transaction_id}")
            
            return jsonify({"status": "success", "message": "Assinatura ativada"}), 200

        else:
            # Ignora eventos que não são relevantes para a nossa lógica
            logging.info(f"Evento {event_type} ignorado. Nenhuma ação necessária.")
            return jsonify({"status": "ignored", "message": f"Evento {event_type} ignorado"}), 200
            
    except Exception as e:
        logging.error(f"Erro ao processar webhook da Kirvano: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Erro interno do servidor"}), 500
