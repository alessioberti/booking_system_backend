from flask import current_app
from flask_mail import Message
from flask_jwt_extended import create_access_token
from app.extensions import mail
from datetime import timezone

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

def send_appointment_confirmation(email, appointment):

    service_name = appointment.service.name
    appointment_date = appointment.appointment_date.strftime("%d/%m/%Y")
    appointment_start_time = appointment.appointment_start_time.strftime("%H:%M")
    appointment_end_time = (appointment.appointment_end_time).strftime("%H:%M")


    subject = "Prenotazioni Centro Medico: Conferma Prenotazione {service_name}"
    body = "La tua prenotazione è stata confermata per il giorno {appointment_date} alle ore {appointment_time} presso "
    msg = Message(subject,
                recipients=[email])
    msg.body = f"{body}"
    mail.send(msg)