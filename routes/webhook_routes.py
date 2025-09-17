
from flask import Blueprint, request, jsonify

webhook_bp = Blueprint('webhook_bp', __name__)

@webhook_bp.route('/webhooks/payments/kirvano', methods=['POST'])
def kirvano_webhook():
    data = request.json  # recebe o payload enviado pelo Kirvano
    print("📩 Webhook recebido da Kirvano:", data)

    # Aqui você pode:
    # - validar o secret do webhook
    # - salvar no banco (ex: ativar assinatura, cancelar, renovar)
    # - retornar resposta para o Kirvano

    return jsonify({"status": "success"}), 200
