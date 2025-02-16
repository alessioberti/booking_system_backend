from app.models.model import Patient, Account, Appointment
from flask import jsonify, make_response, request , current_app
from app.routes import bp
from app import db, mail
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
from flask_jwt_extended import decode_token, create_access_token, set_access_cookies, jwt_required, get_jwt_identity, unset_jwt_cookies, get_jwt
from app.functions.validate_form_data import validate_data
from sqlalchemy import or_, and_
from flask_mail import Message
from uuid import uuid4
from app.functions.send_mail import send_access_token

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

@bp.route('/api/v1/login', methods=['POST'])
def login():
    data = request.json
    if not validate_data(data):
        return jsonify({"error": "Missing or invalid data"}), 400

    # prova a recuperare l'account con username o email
    account = Account.query.filter_by(username=data.get("username")).first()
    if not account:
        account = Account.query.join(Patient).filter_by(email=data.get("username"), is_default=True).first()

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
        return resp, 200
    
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
    return resp, 200

@bp.route('/api/v1/account/password', methods=['PUT'])
@jwt_required()
def change_password():
    current_user = get_jwt_identity()
    data = request.json
    if not data:
        return jsonify({"error": "Missing data"}), 400
    
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

@bp.route('/api/v1/account/patient/update', methods=['PUT'])
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

@bp.route('/api/v1/account/delete', methods=['POST'])
@jwt_required()
def anonimize_account():

    current_user = get_jwt_identity()
    data = request.json
    if not data:
        return jsonify({"error": "Missing data"}), 400
    
    # verifica la password dell'utente
    account = Account.query.get(current_user)
    if account.is_admin:
        return jsonify({"error": "Admin account cannot be deleted"}), 403

    if (not account) or (not (check_password_hash(account.password_hash, data["password"]))):
        return jsonify({"error": "Wrong account or password"}), 401

    
    # verifica se ci sono appuntamenti futuri attivi
    today = datetime.now() 
    appointments_query =  Appointment.query.filter(
            or_(
                Appointment.appointment_date > today.date(),
                and_(Appointment.appointment_time_start == today.time(),Appointment.appointment_time_start >= today.time())
            )
        ).filter_by(account_id=current_user).filter_by(rejected="false")
    
    if appointments_query.first() is not None:
        return jsonify({"error": "Can't delete account with future appointments"}), 409

    # cancella l'account e anonimizza i dati dei pazienti collegati

    try:
        account.anonimize()
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify({"error": "Error in account delete"}), 500

    resp = make_response({"message": "Account deleted"})
    unset_jwt_cookies(resp)
    return resp, 200

@bp.route("/api/v1/forgot", methods=["POST"])
def request_password_reset():
    
    data = request.get_json()
    
    if not validate_data(data):
        return jsonify({"message": "Missing or Invalid data"}), 400
    
    # cerca l'account con username o email
    # prova a recuperare l'account con username o email
    account = Account.query.filter_by(username=data.get("username")).first()
    if not account:
        account = Account.query.join(Patient).filter_by(email=data.get("username"), is_default=True).first()
    if not account:
        return jsonify({"message": "Account not found"}), 404

    email = Patient.query.filter_by(account_id=account.account_id, is_default=True).first().email

    # crea un token valido e crea un link per reimpostare la password
    send_access_token(email, account)
    
    return jsonify({"message": "reset link sent"}), 200

@bp.route("/api/v1/validate", methods=["POST"])
@jwt_required()
def reset_password():
    
    current_user = get_jwt_identity()
    data = request.get_json()

    if not validate_data(data):
        return jsonify({"message": "Missing or Invalid data"}), 400

    account = Account.query.get(current_user)
    if not account:
        return jsonify({"message": "Utente non trovato"}), 404
    
    account.password_hash = generate_password_hash(data.get("password"))
    db.session.commit()

    return jsonify({"message": "Password aggiornata con successo"}), 200

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
        try:

            # crea un nuovo account con una password casuale
            account = Account(
                username=data.get("username"),
                password_hash=generate_password_hash(uuid4().hex),
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

            send_access_token(data.get("email"), account)

        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return jsonify({"error": "Error creating account or patient"}), 500
                            
        return jsonify({"message": "Account created"}), 200
