import os
import click
from app import app, db
from flask_migrate import Migrate
from models import User, Plan, Subscription, Product, Order, OrderItem, CashMovement, CashSession, OrderStatus, RestaurantConfig, Neighborhood, Customer

# Configura o Flask-Migrate
migrate = Migrate(app, db)

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
