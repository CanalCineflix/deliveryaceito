from app import app, db
from flask_migrate import upgrade

with app.app_context():
    # Executa a migração do banco de dados antes de iniciar o servidor
    upgrade()

if __name__ == '__main__':
    # Inicia a aplicação após a migração
    app.run(debug=True, host='0.0.0.0', port=5000)
