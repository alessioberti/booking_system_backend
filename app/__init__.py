from flask import Flask
from app.config import Config
from app.extensions import db
from app.models.model import *
import logging

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.logger.setLevel(app.config['LOG_LEVEL'])
    
    # Initialize the database
    db.init_app(app)

    with app.app_context():
        db.create_all()
        app.logger.info("Database created")
        if app.config['DEMO_DATA'] == "True":
            from app.models.test.test_data import clear_existing_data, insert_demo_data
            app.logger.info("Inserting demo data")
            clear_existing_data()
            insert_demo_data()
            if app.config['TEST_DATA'] == "True":
                from app.models.test.test_data import test_slot_generator
                app.logger.info("Testing slot generator")
                clear_existing_data()
                insert_demo_data()
                test_slot_generator()
    
    # Register the blueprints
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    return app