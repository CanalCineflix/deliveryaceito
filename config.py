import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Configurações do Flask a partir do .env
    FLASK_APP = os.getenv('FLASK_APP')
    FLASK_ENV = os.getenv('FLASK_ENV')
    
    # Configurações do Mercado Pago
    # ... suas outras configurações
    MP_ACCESS_TOKEN = os.environ.get('MP_ACCESS_TOKEN')
    MP_PUBLIC_KEY = os.environ.get('MP_PUBLIC_KEY')
    
    # Configuração do ngrok (se estiver usando)
    NGROK_AUTH_TOKEN = os.getenv('NGROK_AUTH_TOKEN')
    
    # Chave de segurança e banco de dados
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sua-chave-secreta-padrao'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///getsolution.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PAGADOR_EMAIL_TESTE = os.environ.get('PAGADOR_EMAIL_TESTE') or 'test_user@example.com'
