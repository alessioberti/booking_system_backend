from app.models.model import Patient, Account 
from flask import jsonify, make_response, request 
from app.routes import bp
from app import db
import re
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token, set_access_cookies, jwt_required, get_jwt_identity, unset_jwt_cookies, create_refresh_token, set_refresh_cookies, get_jwt
from flask import current_app
from datetime import datetime, timedelta, timezone


# Refresh del token JWT prima della scadenza
@bp.after_request
def refresh_expiring_jwts(response):
    try:
        exp_timestamp = get_jwt()["exp"]
        now = datetime.now(timezone.utc)
        target_timestamp = datetime.timestamp(now + timedelta(minutes=30))
        if target_timestamp > exp_timestamp:
            access_token = create_access_token(identity=get_jwt_identity())
            set_access_cookies(response, access_token)
        return response
    except (RuntimeError, KeyError):
        return response


# Restituisce l'account dell'utente corrente utilizzato per il refresh del token JWT
@bp.route('/api/v1/account', methods=['GET'])
@jwt_required()
def get_account():
    
    current_user = get_jwt_identity()
    account = Account.query.get(current_user)
    if not account:
        return jsonify({"error": "Account not found"}), 404
    else:
        return jsonify(account.to_dict()), 200

# Restituisce il paziente di default associato all'utente corrente
@bp.route('/api/v1/account/patient', methods=['GET'])
@jwt_required()
def get_patient_default():
    
    current_user_id = get_jwt_identity()
    account = Account.query.get(current_user_id)
    if not account:
        return jsonify({"error": "Account not found"}), 404
    else:
        patient = Patient.query.filter_by(account_id=account.account_id, is_default=True).first()
        if not patient:
            return jsonify({"error": "Patient not found"}), 404
        return jsonify(patient.to_dict()), 200

# crea un nuovo account e paziente di default
@bp.route('/api/v1/register', methods=['POST'])
def register():

    try:
        #Almeno una lettera maiuscola, una minuscola, un numero e un simbolo lunghezza da 8 a 32 caratteri
        password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^a-zA-Z0-9]).{8,32}$'
        #Email valida
        email_regex    = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
        #Numero di telefono con o senza prefisso internazionale
        tel_number_regex = r'^\+?\d{10,13}$'
        #campo dodice fiscale accetta solo lettere e numeri (possibilità di inserire un documento straniero )
        fiscal_code_regex = r'^[a-zA-Z0-9]+$'
        #Data di nascita nel formato ISO
        birth_date_regex = r'^\d{4}-\d{2}-\d{2}$'
        # nome e cognome solo lettere apostrofo e spazi
        name_regex = r'^[\w\'\-,.][^0-9_!¡?÷?¿/\\+=@#$%^&*(){}|~<>;:[\]]{2,}$'

        data = request.json

        if not data:
            current_app.logger.error("Missing JSON body")
            return jsonify({"Request invalid":"missing JSON body"}), 400
        if not re.match(password_regex, data.get("password", "")):
            current_app.logger.error("Invalid password")
            return jsonify({"error": "Invalid password"}), 400
        if not re.match(email_regex, data.get("email", "")):
            current_app.logger.error("Invalid email")
            return jsonify({"error": "Invalid email"}), 400
        if not re.match(tel_number_regex, data.get("tel_number", "")):
            current_app.logger.error("Invalid tel_number")
            return jsonify({"error": "Invalid tel_number"}), 400
        if not re.match(fiscal_code_regex, data.get("fiscal_code", "")):
            current_app.logger.error("Invalid fiscal_code")
            return jsonify({"error": "Invalid fiscal_code"}), 400
        if not re.match(birth_date_regex, data.get("birth_date", "")):
            current_app.logger.error("Invalid birth_date")
            return jsonify({"error": "Invalid birth_date"}), 400
        if not re.match(name_regex, data.get("first_name", "")):
            current_app.logger.error("Invalid first_name")
            return jsonify({"error": "Invalid first_name"}), 400
        if not re.match(name_regex, data.get("last_name", "")):
            current_app.logger.error("Invalid last_name")
            return jsonify({"error": "Invalid last_name"}), 400
        
        # verifica se l'email è già in uso altrimenti restituisce un errore 422 

        if Account.query.filter_by(email=data.get("email")).first():
            return jsonify({"error": "Email already in use"}), 422

        account = Account(
            email=data.get("email"),
            password_hash=generate_password_hash(data.get("password"))
        )

        account.create_new(
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            tel_number=data.get("tel_number"),
            fiscal_code=data.get("fiscal_code"),
            birth_date=data.get("birth_date")
        )
        db.session.commit()
        return jsonify({"message": "Account created"}), 200
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify({"error": "Invalid data"}), 400

@bp.route('/api/v1/login', methods=['POST'])
def login():
    data = request.json
    if not data:
        return jsonify({"Request invalid":"missing JSON body"}), 400

    account = Account.query.filter(Account.email == data.get("email")).first()
    
    if not account:
        # per sicurezza non viene comunicato se l'account esiste o meno
        return jsonify({"error": "Invalid email or password"}), 401
    
    # se l'account è disabilitato manda il codice  403 forbbiden
    if not account.enabled:
        return jsonify({"error": "Account disabled"}), 403
    
    # Controlla se ci sono troppi tentativi di accesso falliti
    if (account.failed_login_count >= 5) and ((datetime.now() - account.last_failed_login) < timedelta(minutes=5)):
        return jsonify({"error": "Too many login attempts retry 5 minutes later"}), 409
    
    if check_password_hash(account.password_hash, data["password"]):
        
        # Reset tentativi falliti e aggiorna il database
        account.failed_login_count = 0
        account.last_failed_login = None
        account.last_success_login = datetime.now()
        db.session.commit()
        # Genera il token JWT
        access_token = create_access_token(identity=account.account_id)
        resp = make_response(account.to_dict())
        set_access_cookies(resp, access_token)
        return resp
    
    else:
        # in caso di password errata incrementa i tentativi falliti
        account.failed_login_count += 1
        account.last_failed_login = datetime.now()
        db.session.commit()
        return jsonify({"error": "Invalid email or password"}), 401

@bp.route('/api/v1/logout', methods=['POST'])
def logout():
    resp = make_response({"message": "Logged out"})
    unset_jwt_cookies(resp)
    return resp