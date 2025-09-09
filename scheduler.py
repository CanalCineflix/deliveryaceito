import os
import sys
from datetime import datetime
import logging
from flask import Flask
from dotenv import load_dotenv

# Adiciona o diretório raiz do projeto ao path
# para que as importações funcionem corretamente.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Configuração de logging para registrar o que o scheduler está fazendo
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_app():
    """Cria e configura a aplicação Flask para o contexto do scheduler."""
    app = Flask(__name__)
    app.config.from_object('config.Config')
    
    # Adicione a configuração do banco de dados se não estiver em config.py
    # app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    
    # Importa a instância do SQLAlchemy e a inicializa com o app
    from extensions import db
    db.init_app(app)
    
    return app

def run_scheduler():
    """Função principal do scheduler para processar pagamentos recorrentes."""
    app = create_app()
    with app.app_context():
        # Importações dentro do contexto para evitar erros de importação circular
        try:
            from extensions import db
            from models import Subscription
            from services.payment_service import process_recurrent_payment
        except ImportError as e:
            logging.error(f"Erro ao importar módulos: {e}")
            return

        logging.info("Iniciando a verificação de assinaturas para cobrança.")
        
        # Define a data de corte como agora
        today = datetime.utcnow()

        try:
            # Consulta por assinaturas ativas cuja próxima data de cobrança é hoje ou no passado
            subscriptions_to_charge = Subscription.query.filter(
                Subscription.is_active == True,
                Subscription.next_charge_date <= today
            ).all()

            if not subscriptions_to_charge:
                logging.info("Nenhuma assinatura encontrada para cobrança no momento.")
                return

            logging.info(f"Encontradas {len(subscriptions_to_charge)} assinaturas para processar.")

            for subscription in subscriptions_to_charge:
                try:
                    success = process_recurrent_payment(subscription)
                    if success:
                        logging.info(f"Pagamento recorrente para o usuário {subscription.user_id} processado com sucesso.")
                    else:
                        logging.warning(f"Falha no pagamento recorrente para o usuário {subscription.user_id}.")
                except Exception as e:
                    logging.error(f"Erro ao processar o pagamento para a assinatura {subscription.id}: {e}")

            db.session.commit()
            logging.info("Scheduler de pagamentos concluído com sucesso.")

        except Exception as e:
            db.session.rollback()
            logging.error(f"Ocorreu um erro no scheduler: {e}")
        finally:
            db.session.close()

if __name__ == '__main__':
    run_scheduler()
