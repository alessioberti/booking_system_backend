from app.models.model import Appointment 
from flask import jsonify
from flask import request
from uuid import UUID
from app.routes import bp
from flask import current_app
from app import db

@bp.route('/api/v1/appointment', methods=['GET'])
def get_appointments():
    
    page = request.args.get('page', 1, type=int) if request.args.get('page') else 1
    per_page = request.args.get('per_page', 10, type=int) if request.args.get('per_page') else 10
    
    appointments_query = Appointment.query.paginate(page, per_page, error_out=True)
    
    return jsonify({
        'total': appointments_query.total,
        'pages': appointments_query.pages,
        'current_page': appointments_query.page,
        'data': [appointment.to_dict() for appointment in appointments_query.items]
    })

@bp.route('/api/v1/appointment/<appointment_id>', methods=['GET'])
def get_appointment(appointment_id):
    appointment = Appointment.query.get(UUID(appointment_id))
    if appointment:
        return jsonify(appointment.to_dict())
    return jsonify({"error": "Appointment not found"}), 404

@bp.route('/api/v1/appointment/<appointment_id>/reject', methods=['POST'])
def reject_appointment(appointment_id):
    appointment = Appointment.query.get(UUID(appointment_id))
    if appointment:
        appointment.reject()
        with current_app.transaction():
            pass
        return jsonify(appointment.to_dict())
    return jsonify({"error": "Appointment not found"}), 404

@bp.route('/api/v1/appointment', methods=['POST'])
def create_appointment():
    try:
        data = request.get_json()

        appointment = Appointment()
        appointment.from_dict(data)

        with current_app.transaction():
            db.session.add(appointment)
            db.session.commit()

        return jsonify(appointment.to_dict()), 200
    except Exception as e:
        current_app.logger.error(e)
        return jsonify({"error": "Invalid data"}), 400
    finally:
        db.session.close()