import os

class Config:
    # Use os.environ.get() para carregar a variável de ambiente DATABASE_URL.
    # Isso garante que a aplicação possa encontrar a URL tanto localmente (do .env)
    # quanto na Render (das variáveis de ambiente do servidor).
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
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
