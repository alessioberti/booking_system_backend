from flask import Flask
from app.config import Config
from app.extensions import db, jwt
from flask import jsonify
from contextlib import contextmanager

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.logger.setLevel(app.config['LOG_LEVEL'])
    
    # Inizializzazione delle estensioni
    db.init_app(app)
    jwt.init_app(app)

    # Funzione per gestire le transazioni
    @contextmanager
    def transaction():
        try:
            yield
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Transaction error: {e}")
            raise
        finally:
            db.session.close()

    # Registrazione della funzione transaction come metodo dell'applicazione
    app.transaction = transaction

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
            insert_demo_data_with_tests(10)

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