from app import create_app
from extensions import db

# Criar a instância do aplicativo
app = create_app()

# Entrar no contexto do aplicativo para garantir que o SQLAlchemy funcione
with app.app_context():
    print("Tentando criar todas as tabelas...")
    try:
        db.create_all()
        print("Tabelas criadas com sucesso.")
    except Exception as e:
        print(f"Ocorreu um erro ao criar as tabelas: {e}")
