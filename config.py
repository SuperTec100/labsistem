import os

# Gerar uma chave secreta segura
SECRET_KEY = os.environ.get('SECRET_KEY') or 'sua-chave-secreta-muito-segura-aqui'