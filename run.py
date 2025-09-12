from app import app, db
from flask_migrate import upgrade, current as current_revision, stamp
import os
import sys
import logging

# Configura o logging
logging.basicConfig(level=logging.INFO)

# Apenas para o ambiente de desenvolvimento local, vamos gerenciar as migrações aqui.
# Em produção (Render), o 'render-build.sh' cuidará das dependências.
if __name__ == '__main__':
    with app.app_context():
        try:
            # Tenta aplicar as migrações pendentes
            upgrade()
            logging.info("Migrações aplicadas com sucesso.")
        except Exception as e:
            # Se a migração falhar, o banco de dados pode estar fora de sincronia.
            # Em vez de falhar, vamos registrar o erro.
            # Pode ser necessário um 'stamp' manual em alguns casos, mas a forma
            # mais segura é resolver localmente.
            logging.error(f"Erro ao aplicar migrações: {e}")
    
    # Render usa Gunicorn para servir a aplicação.
    if os.environ.get('RENDER'):
        from gunicorn.app.wsgiapp import WSGIApplication

        class StandaloneApplication(WSGIApplication):
            def __init__(self, app_uri, **kwargs):
                self.app_uri = app_uri
                super().__init__()

            def load_wsgi(self):
                return app
        
        sys.argv = ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
        StandaloneApplication("app:app").run()
    else:
        # Apenas para desenvolvimento local
        app.run(debug=True, host='0.0.0.0', port=5000)
