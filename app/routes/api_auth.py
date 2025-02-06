from app.models.model import Patient, Account 
from flask import jsonify, make_response, request 
from app.routes import bp
from app import db
from flask import current_app
import re, uuid
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token, set_access_cookies, jwt_required, get_jwt_identity, unset_jwt_cookies, create_refresh_token, set_refresh_cookies

@bp.route('/api/v1/mylogin', methods=['GET'])
@jwt_required()
def get_mylogin():
    
    current_user = get_jwt_identity()
    
    account = Account.query.join(Patient.is_default == True).filter(Account.account_id == current_user).first()
    if not account:
        return jsonify({"error": "Account not found"}), 404
    else:
        return jsonify(
                email=account.email,
                tel_number=account.tel_number,
                first_name=account.first_name,
                last_name=account.last_name
            ), 200

@bp.route('/api/v1/register', methods=['POST'])
def register():

    #Almeno una lettera maiuscola, una minuscola, un numero e un simbolo lunghezza da 8 a 32 caratteri
    password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^a-zA-Z0-9]).{8,32}$'
    #Email valida
    email_regex    = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    #Numero di telefono internazionale
    tel_number_regex = r'^\+?\d{10,13}$'

    data = request.json

    if not data:
        return jsonify({"Request invalid":"missing JSON body"}), 400
    if not re.match(password_regex, data.get("password", "")):
        return jsonify({"error": "Invalid password"}), 400
    if not re.match(email_regex, data.get("email", "")):
        return jsonify({"error": "Invalid email"}), 400
    if not re.match(tel_number_regex, data.get("tel_number", "")):
        return jsonify({"error": "Invalid tel_number"}), 400
    if not re.match(r'^[A-Z]{6}[0-9]{2}[A-Z][0-9]{2}[A-Z][0-9]{3}[A-Z]$', data.get("fiscal_code", "")):
        return jsonify({"error": "Invalid fiscal_code"}), 400
    if not re.match(r'^[A-Z][a-z]{1,20}$', data.get("first_name", "")):
        return jsonify({"error": "Invalid first_name"}), 400
    if not re.match(r'^[A-Z][a-z]{1,20}$', data.get("last_name", "")):
        return jsonify({"error": "Invalid last_name"}), 400
    if not re.match(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$', data.get("birth_date", "")):
        return jsonify({"error": "Invalid birth_date"}), 400
    
    if Account.query.filter_by(email=data.get("email")).first():
        return jsonify({"error": "Email already in use"}), 400

    account_uuid = uuid.uuid4()
    new_account = Account(
        account_id=account_uuid,
        password_hash = generate_password_hash(data.get("password")),
        email=data.get("email"),
    )
    new_patient = Patient(
        account_id=account_uuid,
        is_default=True,
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
        email=data.get("email"),
        tel_number=data.get("tel_number"),
        fiscal_code=data.get("fiscal_code"),
        birth_date= datetime.strptime(data.get("birth_date"), "%Y-%m-%d")
    )
    db.session.add(new_account)
    db.session.add(new_patient)
    db.session.commit()  
    
    return jsonify({"message": "Account created"}), 200

@bp.route('/api/v1/login', methods=['POST'])
def login():
    data = request.json
    if not data:
        return jsonify({"Request invalid":"missing JSON body"}), 400

    account = Account.query.filter(Account.email == data.get("email")).first()
    
    if not account:
        # per sicurezza non viene comunicato se l'account esiste o meno
        return jsonify({"error": "Invalid email or password"}), 401
    
    if not account.enabled:
        return jsonify({"error": "Account disabled"}), 401
    
    # Controlla se ci sono troppi tentativi di accesso falliti
    if (account.failed_login_count >= 5) and ((datetime.now() - account.last_failed_login) < timedelta(minutes=5)):
        return jsonify({"error": "Too many login attempts retry 5 minutes later"}), 401
    
    if check_password_hash(account.password_hash, data["password"]):
        
        # Reset tentativi falliti e aggiorna il database
        account.failed_login_count = 0
        account.last_failed_login = None
        account.last_success_logon = datetime.now()
        db.session.commit()
        # Genera il token JWT
        access_token = create_access_token(identity=account.account_id)
        refresh_token = create_refresh_token(identity=account.account_id)

        resp = make_response({"message": "Logged in"})
        set_access_cookies(resp, access_token)
        set_refresh_cookies(resp, refresh_token)
        return resp
    
    else:
        # in caso di password errata incrementa i tentativi falliti
        account.failed_login_count += 1
        account.last_failed_login = datetime.now()
        db.session.commit()
        return jsonify({"error": "Invalid email or password"}), 401

@bp.route('/api/v1/logout', methods=['POST'])
@jwt_required()
def logout():
    resp = make_response({"message": "Logged out"})
    unset_jwt_cookies(resp)
    return resp

@bp.route('/api/v1/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user = get_jwt_identity()
    access_token = create_access_token(identity=current_user)
    resp = make_response({"message": "Token refreshed"})
    set_access_cookies(resp, access_token)
    return resp