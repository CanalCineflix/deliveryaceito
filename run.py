import os
import click
from app import app, db
# Importamos 'stamp' e 'upgrade'
from flask_migrate import Migrate, upgrade, stamp 
from models import User, Plan, Subscription, Product, Order, OrderItem, CashMovement, CashSession, OrderStatus, RestaurantConfig, Neighborhood, Customer
from flask import render_template

# Configura o Flask-Migrate
migrate = Migrate(app, db)

# Adicionamos a rota para /ajuda.html para corresponder ao link no HTML
@app.route('/ajuda.html')
def ajuda():
    return render_template('ajuda.html')

# Adicionamos a nova rota para /juridico.html
@app.route('/juridico.html')
def juridico():
    return render_template('juridico.html')

# Adiciona os modelos ao shell_context para facilitar o uso no `flask shell`
@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Plan=Plan, Subscription=Subscription, Product=Product, Order=Order, OrderItem=OrderItem, CashMovement=CashMovement, CashSession=CashSession, OrderStatus=OrderStatus, RestaurantConfig=RestaurantConfig, Neighborhood=Neighborhood, Customer=Customer)

# Comando CLI para inicialização (Apenas para uso em desenvolvimento local)
@app.cli.command('initdb')
@click.option('--drop', is_flag=True, help='Drops existing tables.')
def initdb_command(drop):
    """Initializes the database (Uso recomendado apenas para desenvolvimento/teste local)."""
    if drop:
        click.confirm('Are you sure you want to drop all tables?', abort=True)
        db.drop_all()
        click.echo('Dropped all tables.')
    db.create_all()
    click.echo('Initialized the database.')
    
@app.cli.command('create_plans')
@click.option('--skip-output', is_flag=True, default=False) # Adicionando flag para controle de output
def create_plans_command(skip_output):
    """Cria os planos Freemium e Premium se eles não existirem."""
    with app.app_context():
        # Verifica e cria/atualiza o Plano Gratuito (Freemium)
        free_plan = Plan.query.filter_by(name='Plano Gratuito').first()
        if not free_plan:
            free_plan = Plan(
                name='Plano Gratuito',
                price=0.00,
                duration_days=15,
                description='Plano gratuito por 15 dias para testar a plataforma.',
                is_free=True
            )
            db.session.add(free_plan)
            if not skip_output:
                click.echo('Plano Gratuito criado.')
        else:
            free_plan.is_free = True
            if not skip_output:
                click.echo('Plano Gratuito atualizado.')

        # Verifica e cria/atualiza o Plano Premium
        premium_plan = Plan.query.filter_by(name='Plano Premium').first()
        if not premium_plan:
            premium_plan = Plan(
                name='Plano Premium',
                price=49.90,
                duration_days=30,
                description='Recursos completos',
                is_free=False,
                kirvano_checkout_url='https://pay.kirvano.com/7344c061-5d52-49c6-8989-ab73b215687f'
            )
            db.session.add(premium_plan)
            if not skip_output:
                click.echo('Plano Premium criado.')
        else:
            # Se o plano já existe, apenas atualiza a URL de checkout
            premium_plan.kirvano_checkout_url = 'https://pay.kirvano.com/7344c061-5d52-49c6-8989-ab73b215687f'
            premium_plan.is_free = False
            if not skip_output:
                click.echo('URL do Plano Premium atualizada.')
            
        db.session.commit()
        if not skip_output:
            click.echo('Planos atualizados com sucesso.')


# NOVA FUNÇÃO DE DEPLOY: Agora com um parâmetro opcional para o stamp
def main_deploy(stamp_only=False):
    """Roda as tarefas de deploy de produção de forma segura: aplica migrações e cria/atualiza planos."""
    with app.app_context():
        if stamp_only:
            # Opção temporária para forçar a sincronização do histórico (fix do erro 'Can't locate revision')
            stamp('head')
            click.echo('Database migration history stamped to HEAD. Deployment will fail to start Gunicorn.')
            click.echo('Please revert the Start Command to the permanent one (Step 2).')
            return # Sai da função após o stamp
            
        # 1. Aplica as migrações do banco de dados. Isso atualiza o schema sem apagar os dados existentes.
        upgrade() 
        click.echo('Database migrations applied.')
        
        # 2. Cria os planos (que você já tinha em create_plans)
        create_plans_command(skip_output=True)
        
        click.echo('Deployment successful.')
        
# O código principal deve continuar a rodar o servidor, mas podemos usar isso para o deploy
if __name__ == '__main__':
    # Se rodarmos diretamente o run.py com o Render, podemos tratar o argumento 'deploy'
    if os.environ.get('FLASK_ENV') == 'development':
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        # Se você está rodando localmente sem gunicorn, ainda pode usar app.run
        app.run(debug=False, host='0.0.0.0', port=5000)
