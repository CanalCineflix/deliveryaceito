from app import app, db
from models import Plan

def create_initial_plans():
    """
    Cria planos iniciais se eles não existirem.
    """
    with app.app_context():
        # Verifica se já existem planos para evitar duplicidade
        if Plan.query.count() == 0:
            print("Criando planos iniciais...")

            # Plano Gratuito
            free_plan = Plan(
                name='Freemium',
                price=0.00,
                description='Acesso gratuito por 15 dias',
                features='15 dias de acesso grátis\nAcesso ao Dashboard Completo\nGerenciamento de Pedidos\nRelatórios de Vendas',
                is_active=True
            )

            # Plano Premium
            premium_plan = Plan(
                name='Premium',
                price=49.90,
                description='Acesso completo por 30 dias',
                features='Acesso completo por 30 dias\nAcesso ao Dashboard Completo\nGerenciamento de Pedidos\nRelatórios de Vendas',
                is_active=True,
                kirvano_checkout_url='https://pay.kirvano.com/7344c061-5d52-49c6-8989-ab73b215687f'
            )

            db.session.add(free_plan)
            db.session.add(premium_plan)
            db.session.commit()
            print("Planos criados com sucesso!")
        else:
            print("Planos já existem no banco de dados. Nenhuma ação necessária.")

if __name__ == '__main__':
    create_initial_plans()
