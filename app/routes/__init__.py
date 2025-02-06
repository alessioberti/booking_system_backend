from flask import Blueprint

bp = Blueprint('routes', __name__)
from app.routes import api_exam, api_appointment, api_auth