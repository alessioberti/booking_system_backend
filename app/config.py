import os
from dotenv import load_dotenv
basedir = os.path.abspath(os.path.dirname(__file__))

# .env per lo sviluppo locale in produzione le variabili d'ambiente sono impostate nel server
env_path = os.path.join(basedir, '../.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

class Config:
    LOG_LEVEL = "INFO"
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL")
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")
    SECRET_KEY = os.environ.get('SECRET_KEY')
    POSTGRES_USER = os.environ.get("POSTGRES_USER")
    POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
    POSTGRES_HOST = os.environ.get("POSTGRES_HOST")
    POSTGRES_DB = os.environ.get("POSTGRES_DB")
    SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}/{POSTGRES_DB}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
    SECRET_KEY = os.environ.get("SECRET_KEY")
    JWT_ALGORITHM = 'HS256'
    JWT_ACCESS_TOKEN_EXPIRES = 3600
    JWT_TOKEN_LOCATION = ["headers", "cookies"]
    JWT_COOKIE_SECURE = True
    JWT_COOKIE_CSRF_PROTECT = True
    JWT_COOKIE_SECURE = True
    JWT_COOKIE_SAMESITE = 'Lax'
    JWT_REFRESH_THRESHOLD_MINUTES = 30
    DEMO_DATA = True
    TEST_DATA = True
    FRONTEND_URL = "https://localhost:5173"
    MAIL_SERVER = "localhost"
    MAIL_PORT = 1025
    MAIL_USE_TLS = False
    MAIL_USE_SSL = False
    MAIL_USERNAME = None
    MAIL_PASSWORD =  None
    MAIL_DEFAULT_SENDER = "noreply@localhost"

  