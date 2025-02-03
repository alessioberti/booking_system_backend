import os
from dotenv import load_dotenv
basedir = os.path.abspath(os.path.dirname(__file__))

# SOLO PER SVILUPPO LOCALE IN PRODUZIONE USARE VARIABILI D'AMBIENTE
env_path = os.path.join(basedir, '../.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

class Config:
    LOG_LEVEL = "INFO"
    SECRET_KEY = os.environ.get('SECRET_KEY')
    POSTGRES_USER = os.environ.get("POSTGRES_USER")
    POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
    POSTGRES_HOST = os.environ.get("POSTGRES_HOST")
    POSTGRES_DB = os.environ.get("POSTGRES_DB")
    SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}/{POSTGRES_DB}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
    JWT_ALGORITHM = 256
    JWT_ACCESS_TOKEN_EXPIRES = 3600
    JWT_REFRESH_TOKEN_EXPIRES = 604800
    JWT_TOKEN_LOCATION = 'cookies'
    JWT_COOKIE_SECURE = False
    JWT_COOKIE_CSRF_PROTECT = False
    JWT_COOKIE_SECURE = False
    ENV = 'development'
    DEMO_DATA = True
    TEST_DATA = True