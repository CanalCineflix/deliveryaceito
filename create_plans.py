# Importa o db do seu arquivo de app (assumindo que o db é instanciado em app.py)
from app import db, app
from models import Plan
from sqlalchemy.exc import IntegrityError

def create_initial_plans():
    """Cria os planos iniciais no banco de dados se eles não existirem."""
    with app.app_context():
        # Verifica se já existem planos
        if Plan.query.count() > 0:
            print("Planos já existem. Nenhum novo plano será criado.")
            return

        print("Criando planos iniciais...")

        # Plano Gratuito (Freemium)
        free_plan = Plan(
            name='Freemium',
            price=0.00,
            description='Acesso básico com recursos limitados.'
        )

        # Plano Premium
        premium_plan = Plan(
            name='Premium',
            price=29.90,
            description='Acesso completo a todos os recursos.'
        )

        # Adiciona os planos à sessão do banco de dados
        db.session.add(free_plan)
        db.session.add(premium_plan)

        try:
            # Comita a transação para salvar os planos
            db.session.commit()
            print("Planos iniciais criados com sucesso!")
        except IntegrityError:
            # Isso pode acontecer se o script for executado várias vezes em paralelo
            db.session.rollback()
            print("Erro de integridade. Planos podem já ter sido criados por outra transação.")
        except Exception as e:
            # Lida com outros possíveis erros durante o commit
            db.session.rollback()
            print(f"Erro ao criar planos: {e}")

if __name__ == '__main__':
    create_initial_plans()
