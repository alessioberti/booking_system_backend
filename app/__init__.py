from flask import Flask
from app.config import Config
from app.extensions import db, jwt
from flask_cors import CORS
from app.models import Account
from werkzeug.security import generate_password_hash

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.logger.setLevel(app.config['LOG_LEVEL'])
    
    # Inizializzazione delle estensioni
    db.init_app(app)
    jwt.init_app(app)

    # Configurazione CORS - abilita solo il frontend
    FRONTEND_URL = app.config['FRONTEND_URL']
    CORS(app, resources={r"/api/*": {"origins": FRONTEND_URL, "supports_credentials": True}})

    # Creazione del database e inserimento dei dati di test in base alla configurazione
    with app.app_context():
        
        db.create_all()
        app.logger.info("Database created")
       
        if app.config['DEMO_DATA'] and not app.config['TEST_DATA']: 
            from app.test import insert_demo_data
            app.logger.info("Inserting demo data")
            insert_demo_data()
            
        elif app.config['TEST_DATA']:
            from app.test import insert_demo_data_with_tests
            app.logger.info("Testing slot generator")
            insert_demo_data_with_tests(1)
    
        # inserisci account di admin se non esiste usando il metodo create_new (crea anche il paziente)
        try:
            existing_admin = Account.query.filter_by(email=app.config['ADMIN_EMAIL']).first()
            if  existing_admin is None:
                    admin = Account(
                            email=app.config['ADMIN_EMAIL'],
                            password_hash = generate_password_hash(app.config['ADMIN_PASSWORD']),
                            is_admin=True
                        )
                    admin.create_new(
                            first_name="Admin",
                            last_name="Admin",
                            tel_number=None,
                            fiscal_code=None,
                            birth_date=None ,
                        )
                    db.session.commit()
                    app.logger.info("Admin %s account created", app.config['ADMIN_EMAIL'])
            else:
                app.logger.info("Admin account already exists")
        except Exception as e:
            app.logger.error(e)
            db.session.rollback()

    # Registrazione delle route tramite blueprint

    from app.routes import bp as routes_bp
    app.register_blueprint(routes_bp)
    app.logger.info(app.url_map)
    
    return app

