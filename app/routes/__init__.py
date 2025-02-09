from flask import Blueprint

bp = Blueprint('routes', __name__)
from app.routes import api_appointment, api_patient, api_auth, api_service