from app import app, db
from models import Plan
from sqlalchemy.exc import IntegrityError
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)

# Dados dos planos a serem criados
PLANS_DATA = [
    {
        "name": "Plano Essencial",
        "description": "Ideal para iniciantes",
        "price": 19.90,
        "duration_days": 30,
        "kirvano_checkout_url": "https://pay.kirvano.com/39a60786-8b2c-4731-97b4-3c87e5b5c7e1"
    },
    {
        "name": "Plano Premium",
        "description": "Recursos completos",
        "price": 49.90,
        "duration_days": 30,
        "kirvano_checkout_url": "https://pay.kirvano.com/d650117b-d298-48b4-9279-d3e75e54d5b7"
    }
]

def create_initial_plans():
    """
    Cria os planos iniciais no banco de dados se eles não existirem.
    """
    with app.app_context():
        try:
            for plan_data in PLANS_DATA:
                existing_plan = Plan.query.filter_by(kirvano_checkout_url=plan_data['kirvano_checkout_url']).first()
                if not existing_plan:
                    new_plan = Plan(**plan_data)
                    db.session.add(new_plan)
                    logging.info(f"Plano '{plan_data['name']}' criado com sucesso.")
                else:
                    logging.info(f"Plano '{plan_data['name']}' já existe. Ignorando a criação.")
            
            db.session.commit()
            logging.info("Todos os planos iniciais foram processados.")

        except IntegrityError:
            db.session.rollback()
            logging.error("Erro de integridade. Planos podem já ter sido criados por outra transação.")
        except Exception as e:
            db.session.rollback()
            logging.error(f"Ocorreu um erro inesperado: {e}")

if __name__ == '__main__':
    create_initial_plans()
