from app.models.model import Appointment, ExamType, Laboratory, Patient, Availability
from flask import jsonify
from flask import request
from uuid import UUID
from app.routes import bp
from flask import current_app
from app import db
from flask_jwt_extended import jwt_required, get_jwt_identity


@bp.route('/api/v1/appointments', methods=['GET'])
@jwt_required()
def get_appointments():
    
    page = request.args.get('page', 1, type=int) if request.args.get('page') else 1
    per_page = request.args.get('per_page', 10, type=int) if request.args.get('per_page') else 10
    
    current_user = get_jwt_identity() 

    # naviga tra le tabelle per ottenere i dati relativi agli appuntamenti
    appointments_query = Appointment.query \
    .join(Availability).join(ExamType).join(Laboratory).join(Patient) \
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
    appointment = Appointment.query.filter_by(id=UUID(appointment_id), account_id=current_user).first()
    
    if appointment:
        return jsonify(appointment.patient.to_dict())
    return jsonify({"error": "Appointment not found"}), 404

@bp.route('/api/v1/appointment', methods=['POST'])
@jwt_required()
def create_appointment():
    try:
        
        current_user = get_jwt_identity()
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid data"}), 400

        patient = data.get("patient")    
        appointment = data.get("appointment")
        appointment["account_id"] = current_user
        
        appointment = Appointment(**appointment)
        appointment.create_new(**patient)
        db.session.commit()

        return jsonify({"success": "Appointment created"}), 200
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify({"error": "Invalid data"}), 400
    finally:
        db.session.close()