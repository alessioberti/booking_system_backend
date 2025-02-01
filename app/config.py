import os
from dotenv import load_dotenv
basedir = os.path.abspath(os.path.dirname(__file__))

load_dotenv(os.path.join(basedir, '.env'))

class Config:
    LOG_LEVEL = os.environ.get('LOG_LEVEL', "INFO")
    SECRET_KEY = os.environ.get('SECRET_KEY')
    POSTGRES_USER = os.environ.get("POSTGRES_USER")
    POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
    POSTGRES_HOST = os.environ.get("POSTGRES_HOST")
    POSTGRES_DB = os.environ.get("POSTGRES_DB")
    SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}/{POSTGRES_DB}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEMO_DATA = os.environ.get("DEMO_DATA", "False")
    TEST_DATA = os.environ.get("TEST_DATA", "False")