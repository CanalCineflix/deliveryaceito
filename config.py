import os

class Config:
    # Use os.environ.get() para carregar a variável de ambiente do banco de dados.
    # A ordem de verificação é importante:
    # 1. 'SQLALCHEMY_DATABASE_URI': para ambientes de desenvolvimento local (como seu .env.local).
    # 2. 'DATABASE_URL': para ambientes de produção (como o Render).
    # 3. 'sqlite:///app.db': um fallback para garantir que sempre haja uma URL de banco de dados.
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or \
                              os.environ.get('DATABASE_URL') or \
                              'sqlite:///app.db'

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'voce-nunca-vai-adivinhar-isso'
    
    # Configurações do Mercado Pago
    MP_ACCESS_TOKEN = os.environ.get('MP_ACCESS_TOKEN')
    MP_PUBLIC_KEY = os.environ.get('MP_PUBLIC_KEY')
    
    # Configurações do Kirvano
    KIRVANO_WEBHOOK_SECRET = os.environ.get('KIRVANO_WEBHOOK_SECRET')

    # Configuração de e-mail (se aplicável)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['seu-email@exemplo.com']
