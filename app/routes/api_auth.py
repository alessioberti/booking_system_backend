from app.models.model import Patient, Account 
from flask import jsonify, make_response, request 
from app.routes import bp
from app import db
import re
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token, set_access_cookies, jwt_required, get_jwt_identity, unset_jwt_cookies, get_jwt
from flask import current_app
from datetime import datetime, timedelta, timezone
from app.functions.validate_form_data import validate_data

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

        data = request.json

        if not validate_data(data):
            return jsonify({"error": "Missing or Invalid data"}), 400
      
        # verifica se l'email è già in uso altrimenti restituisce un errore 422 
        existing_account = Account.query.filter_by(username=data.get("username")).first()
        existing_email = Patient.query.filter_by(email=data.get("email"),is_default = True ).first()

        if existing_account:
            return jsonify({"error": "username_already_exists"}), 422
        if existing_email:
            return jsonify({"error": "email_already_exists"}), 422

        account = Account(
            username=data.get("username"),
            password_hash=generate_password_hash(data.get("password"))
        )

        account.create_new(
            email=data.get("email"),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            tel_number=data.get("tel_number"),
            fiscal_code=data.get("fiscal_code"),
            birth_date=data.get("birth_date")
        )
        db.session.commit()
        return jsonify({"message": "Account created"}), 200

@bp.route('/api/v1/login', methods=['POST'])
def login():
    data = request.json
    if not data:
        return jsonify({"error": "Missing data"}), 400

    # prova a recuperare l'account con username o email
    account = Account.query.filter_by(username=data["username"]).first()
    if not account:
        account = Account.query.join(Patient).filter_by(email=data["username"], is_default=True).first()

    if not account:
        # per sicurezza non viene comunicato se l'account esiste o meno
        return jsonify({"error": "Wrong credentials"}), 401
    
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

@bp.route('/api/v1/account/password', methods=['PUT'])
@jwt_required()
def change_password():
    current_user = get_jwt_identity()
    data = request.json
    if not validate_data(data):
        return jsonify({"error": "Missing or Invalid data"}), 400
    
    account = Account.query.get(current_user)
    if check_password_hash(account.password_hash, data["password"]):
        account.password_hash = generate_password_hash(data["new_password"])
        db.session.commit()
        return jsonify({"message": "Password changed"}), 200
    return jsonify({"error": "Wrong password"}), 401

@bp.route('/api/v1/account/username', methods=['PUT'])
@jwt_required()
def change_user():
    current_user = get_jwt_identity()
    data = request.json

    if not validate_data(data):
        return jsonify({"error": "Missing or Invalid data"}), 400
    
    account = Account.query.get(current_user)
    account.username = data["username"]
    db.session.commit()
    return jsonify({"message": "Username changed"}), 200

@bp.route('/api/v1/account/patient/info', methods=['PUT'])
@jwt_required()
def update_default_patient():
    current_user = get_jwt_identity()
    data = request.json
   
    if not validate_data(data):
        return jsonify({"error": "Missing or Invalid data"}), 400

    account = Account.query.get(current_user)
    patient = Patient.query.filter_by(account_id=account.account_id, is_default=True).first()
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
    patient.first_name = data["first_name"]
    patient.last_name = data["last_name"]
    patient.email = data["email"]
    patient.tel_number = data["tel_number"]
    patient.fiscal_code = data["fiscal_code"]
    patient.birth_date = data["birth_date"]
    db.session.commit()
    return jsonify({"message": "Patient updated"}), 200