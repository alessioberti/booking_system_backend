from flask import current_app
from datetime import datetime, timedelta
import re

BOOKING_WINDOW_DAYS = 365

# regex per la validazione dei campi testuali
regex_rules = {
    "password": r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^a-zA-Z0-9]).{8,32}$',
    "email": r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$',
    "tel_number": r'^\+?\d{7,13}$',
    "fiscal_code": r'[a-zA-Z0-9]{3,32}$',
    "first_name": r"^[A-Za-zÀ-ÖØ-öø-ÿ ,.'-]+$",
    "last_name": r"^[A-Za-zÀ-ÖØ-öø-ÿ ,.'-]+$",
    "username": r'^[A-Za-z0-9@.]{3,32}$'
}
# campi che richiedono la validazione della data
validate_date_fields = ["birth_date", "appointment_date"]

def validate_data(data):
    for key, value in data.items():
        current_app.logger.debug(f"Validating {key}: {value}")
        if key in regex_rules:
            if not re.match(regex_rules[key], value):
                current_app.logger.error(f"Invalid {key}: {value}")
                return False
        if key in validate_date_fields:
            if not value:
                current_app.logger.error(f"Missing {key}")
                return False
            date = datetime.strptime(value, "%Y-%m-%d")
            if (datetime(1900, 1, 1) <= date <= (datetime.now() + timedelta(days=BOOKING_WINDOW_DAYS))):
                continue
            else:
                current_app.logger.error(f"Invalid {key}: {value}")
                return False
    return True