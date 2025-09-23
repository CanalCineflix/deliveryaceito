import os
import click
from app import app, db
from flask_migrate import Migrate
from models import User, Plan, Subscription, Product, Order, OrderItem, CashMovement, CashSession, OrderStatus, RestaurantConfig, Neighborhood, Customer

# Configura o Flask-Migrate
migrate = Migrate(app, db)

from flask import render_template

@app.route('/ajuda')
def ajuda():
    return render_template('ajuda.html')

# Adiciona os modelos ao shell_context para facilitar o uso no `flask shell`
@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Plan=Plan, Subscription=Subscription, Product=Product, Order=Order, OrderItem=OrderItem, CashMovement=CashMovement, CashSession=CashSession, OrderStatus=OrderStatus, RestaurantConfig=RestaurantConfig, Neighborhood=Neighborhood, Customer=Customer)

@app.cli.command('initdb')
@click.option('--drop', is_flag=True, help='Drops existing tables.')
def initdb_command(drop):
    """Initializes the database."""
    if drop:
        click.confirm('Are you sure you want to drop all tables?', abort=True)
        db.drop_all()
        click.echo('Dropped all tables.')
    db.create_all()
    click.echo('Initialized the database.')
    
@app.cli.command('create_plans')
def create_plans_command():
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
            click.echo('Plano Gratuito criado.')
        else:
            free_plan.is_free = True
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
            click.echo('Plano Premium criado.')
        else:
            # Se o plano já existe, apenas atualiza a URL de checkout
            premium_plan.kirvano_checkout_url = 'https://pay.kirvano.com/7344c061-5d52-49c6-8989-ab73b215687f'
            premium_plan.is_free = False
            click.echo('URL do Plano Premium atualizada.')
            
        db.session.commit()
        click.echo('Planos atualizados com sucesso.')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
