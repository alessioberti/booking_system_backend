from flask import current_app
from datetime import datetime
import re

# regex per la validazione dei campi testuali
validate_rules = {
    "password": r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^a-zA-Z0-9]).{8,32}$',
    "email": r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$',
    "tel_number": r'^\+?\d{10,13}$',
    "fiscal_code": r'[a-zA-Z0-9]{3,32}$',
    "first_name": r"^[A-Za-zÀ-ÖØ-öø-ÿ ,.'-]+$",
    "last_name": r"^[A-Za-zÀ-ÖØ-öø-ÿ ,.'-]+$",
    "username": r'^[A-Za-z0-9]{3,32}$',
    "info": r'^[A-Za-zÀ-ÖØ-öø-ÿ0-9\s.,;:\'"?!()\-]{1,500}$'
}
# campi che richiedono la validazione della data
validate_date_fields = ["birth_date", "appointment_date"]

def validate_data(data):
    if not data:
        current_app.logger.error("Missing data")
        return False
    for field, value in data.items():
        current_app.logger.info(f"Validating {field}: {value}")
        # se il campo è la data di nascita esegui il controllo della data
        if field in validate_date_fields:
            date = datetime.strptime(value, "%Y-%m-%d")
            if (datetime(1900, 1, 1) <= date <= datetime.now()):
                continue
            else:
                current_app.logger.error(f"Invalid {field}: {value}")
                return False
        # per tutti gli altri campi, esegui il controllo regex
        elif field in validate_rules:
            if not re.match(validate_rules[field], value):
                current_app.logger.error(f"Invalid {field}: {value}")
                return False
    return True