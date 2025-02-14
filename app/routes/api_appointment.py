from app.models.model import Appointment, Service, Location, Patient, Availability
from flask import jsonify
from flask import request
from uuid import UUID
from app.routes import bp
from flask import current_app
from app import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.functions.validate_form_data import validate_data
from datetime import datetime
from sqlalchemy import or_, and_

# restituisce tutti gli appuntamenti associati all'utente corrente
@bp.route('/api/v1/appointments', methods=['GET'])
@jwt_required()
def get_appointments():
    
    # converte i parametri della query string in booleani in base al valore fornito
    rejected_appointments = request.args.get('rejected_appointments', 'false').lower() == 'true'
    past_appointments = request.args.get('past_appointments', 'false').lower() == 'true'
   
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    current_user = get_jwt_identity() 

    # naviga tra le tabelle per ottenere i dati relativi agli appuntamenti ordinati per data e ora
    appointments_query = Appointment.query.join(Availability).join(Service).join(Location).join(Patient).filter(Appointment.account_id == current_user)
  
    # se non stati specificati appuntamenti rifiutati, filtra gli appuntamenti rifiutati
    if rejected_appointments == False:
        appointments_query = appointments_query.filter(Appointment.rejected == False)

    # se non sono stati specificati appuntamenti passati, filtra gli appuntamenti passati
    if past_appointments == False:
        today = datetime.now()
        appointments_query = appointments_query = appointments_query.filter(
            or_(
                Appointment.appointment_date > today.date(),
                and_(Appointment.appointment_time_start == today.time(),Appointment.appointment_time_start >= today.time())
            )
        )

    appointments_query =  appointments_query.order_by(Appointment.appointment_date.desc(), Appointment.appointment_time_start.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    # usa il metodo to_dict per ottenere solo i dati necessari e restiuici un json 
    return jsonify({
        'total': appointments_query.total,
        'pages': appointments_query.pages,
        'current_page': appointments_query.page,
        'data': [appointment.to_dict() for appointment in appointments_query.items]
    })

# crea un nuovo appuntamento e paziente associato
@bp.route('/api/v1/appointment', methods=['POST'])
@jwt_required()
def create_appointment():

        current_user = get_jwt_identity()
        data = request.get_json()
        patient_data = data.get("patient")    
        appointment_data = data.get("appointment")

        if not validate_data(patient_data):
            return jsonify({"error": "Invalid patient_datata"}), 400
        if not validate_data(appointment_data):
            return jsonify({"error": "Invalid appointment_data"}), 400
        
        # crea un nuovo appuntamento
        appointment = Appointment(
            availability_id = appointment_data.get("availability_id"),
            appointment_date = appointment_data.get("appointment_date"),
            appointment_time_start = appointment_data.get("appointment_time_start"),
            appointment_time_end = appointment_data.get("appointment_time_end"),
            info = appointment_data.get("info"),
            account_id = current_user
        )

        # usa il metodo create_new per creare un nuovo paziente e associarlo all'appuntamento
        appointment.create_new(
            patient_first_name = patient_data.get("first_name"),
            patient_last_name = patient_data.get("last_name"),
            patient_email = patient_data.get("email"),
            patient_tel_number = patient_data.get("tel_number"),
            patient_fiscal_code = patient_data.get("fiscal_code"),
            patient_birth_date = patient_data.get("birth_date"),
            patient_is_default = patient_data.get("is_default")
        )
        db.session.commit()

        return jsonify({"success": "Appointment created"}), 200

# restituisce i dati di un appuntamento
@bp.route('/api/v1/appointments/<appointment_id>', methods=['GET'])
@jwt_required()
def get_appointment(appointment_id):
    appointment = Appointment.query.get(UUID(appointment_id))
    if appointment:
        return jsonify(appointment.to_dict())
    return jsonify({"error": "Appointment not found"}), 404

# sostituisce un appuntamento con un altro
@bp.route('/api/v1/appointments/<appointment_id>/replace', methods=['PUT'])
@jwt_required()
def replace_appointment(appointment_id):
    
    current_user = get_jwt_identity()
    data = request.get_json()
    patient_data = data.get("patient")
    appointment_data = data.get("appointment")
    
    if not validate_data(patient_data):
        return jsonify({"error": "Invalid patient_data"}), 400
    if not validate_data(appointment_data):
        return jsonify({"error": "Invalid appointment_data"}), 400

    # recupera l'appuntamento e verifica che l'account associato sia l'utente corrente
    appointment = Appointment.query.filter_by(appointment_id=UUID(appointment_id), account_id=current_user).first()
    if not appointment:
        current_app.logger.error("Appointment %s not found for current user %s", appointment_id, current_user)
        return jsonify({"error": "Appointment not found"}), 404

    try:

         # crea un nuovo appuntamento
        new_appointment = Appointment(
            availability_id = appointment_data.get("availability_id"),
            appointment_date = appointment_data.get("appointment_date"),
            appointment_time_start = appointment_data.get("appointment_time_start"),
            appointment_time_end = appointment_data.get("appointment_time_end"),
            info = appointment_data.get("info"),
            account_id = current_user
        )

        # usa il metodo create_new per creare un nuovo paziente e associarlo all'appuntamento
        new_appointment.create_new(
            patient_first_name = patient_data.get("first_name"),
            patient_last_name = patient_data.get("last_name"),
            patient_email = patient_data.get("email"),
            patient_tel_number = patient_data.get("tel_number"),
            patient_fiscal_code = patient_data.get("fiscal_code"),
            patient_birth_date = patient_data.get("birth_date"),
            patient_is_default = patient_data.get("is_default")
        )

        # sostituisci l'appuntamento con il nuovo appuntamento
        db.session.delete(appointment)
        db.session.commit()
        return jsonify("Appointment replaced"), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify({"error": "Invalid data"}), 400

# cancella un appuntamento
@bp.route('/api/v1/appointments/<appointment_id>/reject', methods=['PUT'])
@jwt_required()
def reject_appointment(appointment_id):
    
    try:
        appointment = Appointment.query.get(UUID(appointment_id))
        appointment.rejected = True
        db.session.commit()
        return jsonify(appointment.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify({"error": "Invalid data"}), 400

# modifica le info dell'appuntamento
@bp.route('/api/v1/appointments/<appointment_id>/info', methods=['PUT'])
@jwt_required()
def edit_appointment(appointment_id):
    
    current_user = get_jwt_identity()
    data = request.get_json()
    if not validate_data(data):
        return jsonify({"error": "Invalid data"}), 400

    appointment = Appointment.query.filter_by(appointment_id=UUID(appointment_id), account_id=current_user).first()
    
    if not appointment:
        current_app.logger.error("Appointment %s not found for current user %s", appointment_id, current_user)
        return jsonify({"error": "Appointment not found"}), 404    
    try:    
        appointment.info = data.get("info")
        db.session.commit()
        return jsonify('Appointment info updated'), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify({"error": "Invalid data"}), 400

# restituisce i dati del paziente associato all'appuntamento
@bp.route('/api/v1/appointments/<appointment_id>/patient', methods=['GET'])
@jwt_required()
def get_appointment_patient(appointment_id):
    
    current_user = get_jwt_identity()
    # restituisce i dati del paziente associato all'appuntamento e all'utente corrente
    appointment = Appointment.query.filter_by(appointment_id=UUID(appointment_id), account_id=current_user).first()
    
    if appointment:
        return jsonify(appointment.patient.to_dict())
    return jsonify({"error": "Appointment not found"}), 404

# modifica i dati del paziente associato all'appuntamento se il paziente non è di default
@bp.route('/api/v1/appointments/<appointment_id>/patient/update', methods=['PUT'])
@jwt_required()
def edit_appointment_patient(appointment_id):
    
    current_user = get_jwt_identity()
    data = request.get_json()
 
    patient_data = data.get("patient")
    if not validate_data(patient_data):
        return jsonify({"error": "Invalid patient_data"}), 400

    # recupera l'appuntamento e verifica che l'account associato sia l'utente corrente
    appointment = Appointment.query.filter_by(appointment_id=UUID(appointment_id), account_id=current_user).first()
    if not appointment:
        current_app.logger.error("Appointment %s not found for current user %s", appointment_id, current_user)
        return jsonify({"error": "Appointment not found"}), 404
    
    # controlla che il paziente non sia di default e che l'id del paziente corrisponda a quello fornito
    if appointment.patient.is_default:
        current_app.logger.error("Default patient cannot be updated")
        return jsonify({"error": "Default patient cannot be updated"}), 409
        
    if appointment.patient_id == patient_data.get("patient_id"):
        current_app.logger.error("Unable to update patient_id %s", patient_data.get("patient_id")  )
        return jsonify({"error": "Patient id mismatch"}), 409
    
    appointment.patient.first_name = patient_data.get("first_name")
    appointment.patient.last_name = patient_data.get("last_name")
    appointment.patient.tel_number = patient_data.get("tel_number")
    appointment.patient.fiscal_code = patient_data.get("fiscal_code")
    appointment.patient.birth_date = patient_data.get("birth_date")
    db.session.commit()
    return jsonify(appointment.patient.to_dict())
    
# sostituisce il paziente associato all'appuntamento
@bp.route('/api/v1/appointments/<appointment_id>/patient/replace', methods=['PUT'])
@jwt_required()
def replace_appointment_patient(appointment_id):
    
    current_user = get_jwt_identity()
    data = request.get_json()
    patient_data = data.get("patient")
    if not validate_data(patient_data):
        return jsonify({"error": "Invalid patient_data"}), 400

    # recupera l'appuntamento e verifica che l'account associato sia l'utente corrente
    appointment = Appointment.query.filter_by(appointment_id=UUID(appointment_id), account_id=current_user).first()
    if not appointment:
        current_app.logger.error("Appointment %s not found for current user %s", appointment_id, current_user)
        return jsonify({"error": "Appointment not found"}), 404
    try:
        # crea un nuovo paziente e lo associa all'appuntamento
        new_patient = Patient(
            first_name = patient_data.get("first_name"),
            last_name = patient_data.get("last_name"),
            email = patient_data.get("email"),
            tel_number = patient_data.get("tel_number"),
            fiscal_code = patient_data.get("fiscal_code"),
            birth_date = patient_data.get("birth_date"),
            is_default = False,
            account_id = current_user
        )
        # aggiungi il nuovo paziente al database
        db.session.add(new_patient)
        # esegui il flush per ottenere l'id del nuovo paziente
        db.session.flush()
        # associa il nuovo paziente all'appuntamento
        appointment.patient_id = new_patient.patient_id
    
        db.session.commit()
        return jsonify("Patient replaced"), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify({"error": "Invalid data"}), 400

