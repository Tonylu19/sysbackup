import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "clave-secreta-local"
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(basedir, 'app.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(basedir, 'backups')
    CIPHER_KEY = os.environ.get("CIPHER_KEY") or "32_bytes_aes_encryption_key_123456"

# Puerto para Render (o por defecto 10000 en local)
PORT = int(os.environ.get("PORT", 10000))
