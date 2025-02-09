from app.models.model import Patient, Account
from flask import jsonify
from app.routes import bp
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import request
from werkzeug.security import generate_password_hash
from datetime import datetime
