from flask import current_app
from flask_mail import Message
from flask_jwt_extended import create_access_token
from app.extensions import mail
from datetime import timedelta

# le mail vengono inviate con il metodo send_mail e localizzato in italiano

def send_access_token(email, account):
    access_token = create_access_token(identity=account.account_id)
    reset_url = f"{current_app.config['FRONTEND_URL']}/validate-account?token={access_token}"

    subject = "Prenotazioni Centro Medico: Validazione Password"
    body = "Usa il seguente link per reimpostare la tua password"

    msg = Message(subject,
                recipients=[email])
    msg.body = f"{body}: {reset_url}"
    mail.send(msg)

def send_appointment_confirmation(email, service_name, patient_name, appointment):

    appointment_date = appointment.appointment_date.strftime("%d/%m/%Y")
    appointment_time_start = appointment.appointment_time_start.strftime("%H:%M")
    appointment_time_end = (appointment.appointment_time_end).strftime("%H:%M")

    subject = f"Conferma prenotazione {service_name} per {patient_name}"
    body = f"La prenotazione per {patient_name} del {appointment_date} dalle {appointment_time_start} alle {appointment_time_end} è stata confermata"
    msg = Message(subject,
                recipients=[email])
    msg.body = f"{body}"
    mail.send(msg)


def send_appointment_cancellation(email, service_name, patient_name, appointment):
 
    appointment_date = appointment.appointment_date.strftime("%d/%m/%Y")
    appointment_time_start = appointment.appointment_time_start.strftime("%H:%M")
    appointment_time_end = (appointment.appointment_time_end).strftime("%H:%M")

    subject = f"Conferma cancellazione {service_name} per {patient_name}"
    body = f"La prenotazione per {patient_name} del {appointment_date} dalle {appointment_time_start} alle {appointment_time_end} è stata cancellata"
    msg = Message(subject,
                recipients=[email])
    msg.body = f"{body}"
    mail.send(msg)
