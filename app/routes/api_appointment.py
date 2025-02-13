from app.models.model import Appointment, Service, Location, Patient, Availability
from flask import jsonify
from flask import request
from uuid import UUID
from app.routes import bp
from flask import current_app
from app import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.functions.validate_form_data import validate_data

@bp.route('/api/v1/appointments', methods=['GET'])
@jwt_required()
def get_appointments():
    
    page = request.args.get('page', 1, type=int) if request.args.get('page') else 1
    per_page = request.args.get('per_page', 10, type=int) if request.args.get('per_page') else 10
    
    current_user = get_jwt_identity() 

    # naviga tra le tabelle per ottenere i dati relativi agli appuntamenti
    appointments_query = Appointment.query \
    .join(Availability).join(Service).join(Location).join(Patient) \
    .filter(Appointment.account_id == current_user) \
    .paginate(page=page, per_page=per_page, error_out=True)

    # usa il metodo to_dict per ottenere solo i dati necessari e restiuici un json 
    return jsonify({
        'total': appointments_query.total,
        'pages': appointments_query.pages,
        'current_page': appointments_query.page,
        'data': [appointment.to_dict() for appointment in appointments_query.items]
    })

@bp.route('/api/v1/appointments/<appointment_id>', methods=['GET'])
@jwt_required()
def get_appointment(appointment_id):
    appointment = Appointment.query.get(UUID(appointment_id))
    if appointment:
        return jsonify(appointment.to_dict())
    return jsonify({"error": "Appointment not found"}), 404

@bp.route('/api/v1/appointments/<appointment_id>/reject', methods=['PUT'])
@jwt_required()
def reject_appointment(appointment_id):
    
    try:
        appointment = Appointment.query.get(UUID(appointment_id))
        appointment.rejected = True
        db.session.commit()
        return jsonify(appointment.to_dict()), 200
    except Exception as e:
        current_app.logger.error(e)
        return jsonify({"error": "Invalid data"}), 400

@bp.route('/api/v1/appointments/<appointment_id>/patient', methods=['GET'])
@jwt_required()
def get_appointment_patient(appointment_id):
    
    current_user = get_jwt_identity()
    # restituisce i dati del paziente associato all'appuntamento e all'utente corrente
    appointment = Appointment.query.filter_by(appointment_id=UUID(appointment_id), account_id=current_user).first()
    
    if appointment:
        return jsonify(appointment.patient.to_dict())
    return jsonify({"error": "Appointment not found"}), 404

@bp.route('/api/v1/appointment', methods=['POST'])
@jwt_required()
def create_appointment():

        current_user = get_jwt_identity()
        data = request.get_json()
        patient_data = data.get("patient")    
        appointment_data = data.get("appointment")

        if not validate_data(patient_data):
            return jsonify({"error": "Invalid data"}), 400
        if not validate_data(appointment_data):
            return jsonify({"error": "Invalid data"}), 400
        
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

@bp.route('/api/v1/appointments/<appointment_id>/info', methods=['PUT'])
@jwt_required()
def edit_appointment(appointment_id):
    
    current_user = get_jwt_identity()
    data = request.get_json()
    if not validate_data(data):
        return jsonify({"error": "Invalid data"}), 400

    appointment = Appointment.query.filter_by(appointment_id=UUID(appointment_id), account_id=current_user).first()
    
    if appointment:
        appointment.info = data.get("info")
        db.session.commit()
        return jsonify(appointment.to_dict())
    return jsonify({"error": "Appointment not found"}), 404

# modifica i dati del paziente associato all'appuntamento se il paziente non è di default
@bp.route('/api/v1/appointments/<appointment_id>/patient', methods=['PUT'])
@jwt_required()
def edit_appointment_patient(appointment_id):
    
    current_user = get_jwt_identity()
    data = request.get_json()
 
    patient_data = data.get("patient")
    if not validate_data(patient_data):
        return jsonify({"error": "Invalid data"}), 400

    # recupera i dati del paziente associato all'appuntamento e all'utente corrente
    patient = Appointment.query.join(Patient).filter_by(appointment_id=UUID(appointment_id), account_id=current_user, patient_id=UUID(patient_data.get("patient_id"))).first()

    # se l'appuntamento esiste e il paziente non è di default aggiorna i dati del paziente  
    if patient and patient_data.get("is_default") == False:
        patient.first_name = patient_data.get("first_name")
        patient.last_name = patient_data.get("last_name")
        patient.tel_number = patient_data.get("tel_number")
        patient.fiscal_code = patient_data.get("fiscal_code")
        patient.birth_date = patient_data.get("birth_date")
        db.session.commit()
        return jsonify(patient.to_dict())
    return jsonify({"error": "Unable to update"}), 404
