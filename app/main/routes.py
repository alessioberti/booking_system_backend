from app.main import bp
from app.models.model import db, Account, Laboratory, Patient, Availability, Operator, ExamType
from flask import jsonify

bp.route('api/v1/exam_type', methods=['GET'])
def get_exam_types():
    exam_types = ExamType.query.all()
    return jsonify([exam_type.to_dict() for exam_type in exam_types])

@bp.route('/api/v1/availability', methods=['GET'])
def get_availabilities():
    availabilities = Availability.query.all()
    return jsonify([availability.to_dict() for availability in availabilities])

@bp.route('/api/v1/availability/<availability_id>', methods=['GET'])
def get_availability(availability_id):
    availability = Availability.query.get(availability_id)
    return jsonify(availability.to_dict())
