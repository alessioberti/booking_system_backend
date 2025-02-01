from flask import Flask
from app.config import Config
from app.extensions import db
import logging
from app.models.model import *

logging.basicConfig(level=logging.INFO)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize the database
    db.init_app(app)

    with app.app_context():
        db.create_all()
        logging.info("Database created")
        if app.config['DEMO_MODE']:
            from app.models.demo_data import clear_existing_data, insert_demo_data
            clear_existing_data()
            insert_demo_data()
    
    # Register the blueprints
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    return app