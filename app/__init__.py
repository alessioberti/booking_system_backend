from flask import Flask
from app.config import Config
from app.extensions import db, jwt
from flask_cors import CORS
from flask import jsonify
from app.models import Account
from werkzeug.security import generate_password_hash
import uuid
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
    
    # Registrazione degli error handler globali
    register_error_handlers(app)
    
    return app

def register_error_handlers(app):
    @app.errorhandler(404)
    def page_not_found(error):
        app.logger.error(f"Page Not Found: {error}")
        return jsonify({"error": 404, "message": "Not Found"}), 404
    @app.errorhandler(500)
    def internal_server_error(error):
        app.logger.error(f"Internal Server Error: {error}")
        return jsonify({"error": 500, "message": "Internal Server Error"}), 500
    @app.errorhandler(400)
    def bad_request(error):
        app.logger.error(f"Bad Request: {error}")
        return jsonify({"error": 400, "message": "Bad Request"}), 400
    @app.errorhandler(405)
    def method_not_allowed(error):
        app.logger.error(f"Method Not Allowed: {error}")
        return jsonify({"error": 405, "message": "Method Not Allowed"}), 405
    @app.errorhandler(403)
    def forbidden(error):
        app.logger.error(f"Forbidden: {error}")
        return jsonify({"error": 403, "message": "Forbidden"}), 403
    @app.errorhandler(401)
    def unauthorized(error):
        app.logger.error(f"Unauthorized: {error}")
        return jsonify({"error": 401, "message": "Unauthorized"}), 401