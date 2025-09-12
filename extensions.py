from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# Inicializa as extensões sem a aplicação Flask, evitando importações circulares.
# A inicialização é feita mais tarde no arquivo app.py
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
