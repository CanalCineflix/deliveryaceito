import json
from flask import Blueprint, request, jsonify
from services.user_service import handle_kirvano_webhook
import logging
import os

# Configuração de logging para depuração
logging.basicConfig(level=logging.INFO)

payments_bp = Blueprint('payments', __name__, url_prefix='/payments')

@payments_bp.route('/kirvano', methods=['POST'])
def kirvano_webhook():
    """
    Endpoint único para receber todos os webhooks da Kirvano.
    Ele chama a função de serviço para lidar com o evento.
    """
    try:
        # 1. Obtém o token de segurança do header da requisição
        kirvano_token = request.headers.get('X-Kirvano-Token')
        
        # 2. Obtém o token salvo nas variáveis de ambiente
        expected_token = os.environ.get('KIRVANO_WEBHOOK_SECRET')

        # 3. Verifica se o token existe e se corresponde
        if not kirvano_token or kirvano_token != expected_token:
            logging.error("Requisição de webhook não autorizada. Token inválido.")
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

        data = request.json
        event_type = data.get('event_type')
        payload = data.get('payload')

        # Loga o evento recebido para depuração
        logging.info(f"Webhook da Kirvano recebido. Tipo de Evento: {event_type}")

        # Verifica se o webhook é válido
        if not event_type or not payload:
            logging.error("Dados do webhook ausentes ou inválidos.")
            return jsonify({'status': 'error', 'message': 'Invalid data'}), 400

        # Chama a função de serviço para lidar com o evento
        handle_kirvano_webhook(event_type, payload)
        
        return jsonify({'status': 'success', 'message': 'Webhook processed'}), 200

    except Exception as e:
        # Loga o erro com detalhes para facilitar a depuração
        logging.error(f"Erro ao processar o webhook: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Internal Server Error'}), 500
