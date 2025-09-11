from app import app, db
from flask_migrate import upgrade
import os
import sys

# Se a aplicação estiver sendo executada no ambiente do Render (ou qualquer ambiente de produção),
# o comando 'gunicorn' será usado para iniciar o servidor. Nesse caso, a migração não precisa ser executada
# por este script, pois o comando de pre-deploy já cuidará disso.
# Esta é a abordagem mais segura para evitar problemas.
if __name__ == '__main__':
    with app.app_context():
        upgrade() # Garante que as migrações sejam aplicadas antes de iniciar o servidor
    
    # Render usa Gunicorn para servir a aplicação.
    # Em produção, você deve usar o Gunicorn para rodar a aplicação.
    if os.environ.get('RENDER'):
        from gunicorn.app.wsgiapp import WSGIApplication

        class StandaloneApplication(WSGIApplication):
            def __init__(self, app_uri, **kwargs):
                self.app_uri = app_uri
                super().__init__()

            def load_wsgi(self):
                return app
        
        # O Gunicorn precisa do comando 'gunicorn app:app' para rodar,
        # mas como estamos em um script de inicialização, podemos chamar a classe
        # do Gunicorn diretamente.
        sys.argv = ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
        StandaloneApplication("app:app").run()
    else:
        # Apenas para desenvolvimento local
        app.run(debug=True, host='0.0.0.0', port=5000)
