from flask import current_app
from app.models.model import db, Account, Laboratory, Patient, Availability, Operator, ExamType, LaboratoryClosure, OperatorAbsence, Appointment
from app.models.generate_available_slots_v1 import generate_available_slots
import uuid
from datetime import date, time, datetime, timedelta
import random

def generate_random_datetime(min_date: date, max_date: date) -> datetime:
    delta_days = (max_date - min_date).days
    random_days = random.randint(0, delta_days)
    return datetime.combine(min_date + timedelta(days=random_days), datetime.min.time())

import uuid
import random
from app.models.model import db, Account, Patient, Laboratory, LaboratoryClosure, ExamType, Operator, OperatorAbsence, Availability, Appointment

def insert_patients_operators(numberof_patients=1, numberof_operators=1):

    FIRST_NAME_LIST = ["Alessio","Davide","Mauro","Roberto","Maurizio","Giovanni","Giovanna","Milena","Antonio","Alessia","Mirko","Maura","Roberta","Fabio","Giuseppe","Federica"]
    LAST_NAME_LIST = ["Arancioni","Verdi","Azzurri","Rosa","Celesti","Verdi","Blu","Bianchi","Neri","Gialli","Arancioni","Viola","Marroni","Neri","Gialli","Rossi"]

    already_created_emails = []

    for i in range(numberof_patients):

        try:    
            email = ""
            for j in range(len(FIRST_NAME_LIST) * len(LAST_NAME_LIST)):
                first_name = random.choice(FIRST_NAME_LIST)
                last_name = random.choice(LAST_NAME_LIST)
                email = f"{first_name.lower()}.{last_name.lower()}@gmail.com"
                if email not in already_created_emails:
                    already_created_emails.append(email)
                    break
                
            if email == "":
                current_app.logger.warning("Cannot generate unique email for patient skipping.")
                continue

            account_uuid = uuid.uuid4()
            patient_uuid = uuid.uuid4()

            account = Account(
                account_id=account_uuid,
                email=email,
                password_hash="hashed_password",
                enabled=True,
            )
            patient = Patient(
                patient_id=patient_uuid,
                account_id=account_uuid,
                is_default=True,
                first_name=first_name,
                last_name=last_name,
                email=account.email,
                tel_number="+391234567890",
                fiscal_code="FISCALCODE123456",
                birth_date=datetime(random.randint(1950, 2000), random.randint(1, 12), random.randint(1, 28)),
                anonimized=False
            )

            db.session.add(account)
            db.session.add(patient)
            db.session.commit()
        except Exception as e:
            current_app.logger.error("Error inserting patient: %s", e)
            db.session.rollback()
            continue

    for i in range(numberof_operators):

        try:
            email = ""
            for j in range(len(FIRST_NAME_LIST) * len(LAST_NAME_LIST)):
                first_name = random.choice(FIRST_NAME_LIST)
                last_name = random.choice(LAST_NAME_LIST)
                email = f"{first_name.lower()}.{last_name.lower()}@gmail.com"
                if email not in already_created_emails:
                    already_created_emails.append(email)
                    break
                
            if email == "":
                current_app.logger.warning("Cannot generate unique email for operator skipping.")
                continue

            first_name = random.choice(FIRST_NAME_LIST)
            last_name = random.choice(LAST_NAME_LIST)
            account_uuid = uuid.uuid4()
            operator_uuid = uuid.uuid4()

            account = Account(
                account_id=account_uuid,
                email=email,
                password_hash="hashed_password",
                enabled=True,
                is_operator=True
            )
            operator = Operator(
                operator_id=operator_uuid,
                account_id=account_uuid,
                title="Dott.",
                first_name=first_name,
                last_name=last_name
            )
            db.session.add(account)
            db.session.add(operator)
            db.session.commit()
        except Exception as e:
            current_app.logger.error("Error inserting operator: %s", e)
            db.session.rollback()
            continue

def insert_laboratories(numberof_laboratories=1):

    LOCATION_LIST = ["L'Acquila","Chieti","Pescara","Catanzaro","Firenze","Teramo","Bari","Palermo","Genova","Catania","Brescia","Cosenza","Taranto","Prato","Modena"]

    for i in range(numberof_laboratories):
        
        try:
            lab_uuid = uuid.uuid4()
            lab = Laboratory(
                laboratory_id=lab_uuid,
                name=f"Laboratorio {random.choice(LOCATION_LIST)}",
                address=f"Via {random.choice(LOCATION_LIST)} {random.randint(1, 100)}",
                tel_number="+391234567890"
            )
            db.session.add(lab)
            db.session.commit()
        except Exception as e:
            current_app.logger.error("Error inserting laboratory: %s", e)
            db.session.rollback()
            continue

def insert_exam_types(numberof_exam_types=1):

    EXAM_NAME_LIST = ["Visita Oculistica", "Visita Otorinolaringoiatrica", "Visita Cardiologica", "Visita Dermatologica", "Visita Ginecologica", "Visita Ortopedica", "Visita Pediatria", "Visita Psicologica", "Visita Urologica", "Visita Neurologica", "Visita Endocrinologica"]
    
    while len(ExamType.query.all()) < numberof_exam_types:
        
        if len(ExamType.query.all()) == len(EXAM_NAME_LIST):
            break

        for exam_mame in EXAM_NAME_LIST:
            try:
                exam_type = ExamType(
                    exam_type_id=uuid.uuid4(),
                    name = exam_mame,
                    description="Descrizione esame " + exam_mame
                )
                db.session.add(exam_type)
                db.session.commit()
            except Exception as e:
                current_app.logger.error("Error inserting exam type: %s", e)
                db.session.rollback()
                continue

def insert_availabilities(numberof_availabilities=1):

    AVAILABILITY_DATETTIME_START = datetime.today()

    SLOT_DURATION_LIST = [15, 30, 45, 60]
    PAUSE_DURATION_LIST = [0, 5, 10, 15]
    AVAILABILITY_START_LIST = [time(8, 0), time(9, 0), time(10, 0), time(11, 0)]
    
    while len(Availability.query.all()) < numberof_availabilities:
        
        try:
            # crea una disponibilità casuale
            available_from_date= AVAILABILITY_DATETTIME_START
            available_to_date=(available_from_date + timedelta(days=30 * random.randint(3, 6)))
            available_from_time=random.choice(AVAILABILITY_START_LIST)
            available_to_time = (datetime.combine(available_from_date, available_from_time) + timedelta(hours=random.randint(4, 10))).time()
            
            # calcola i giorni della settimana in cui è disponibile coerentemente con la data di inizio e fine
            total_days = (available_to_date - available_from_date).days
            weekdays_available = [(available_from_date.weekday() + offset) % 7 for offset in range(total_days)]

            availability = Availability(
                availability_id=uuid.uuid4(),
                exam_type_id=random.choice(ExamType.query.all()).exam_type_id,
                laboratory_id=random.choice(Laboratory.query.all()).laboratory_id,
                operator_id=random.choice(Operator.query.all()).operator_id,
                available_from_date=available_from_date,
                available_to_date=available_to_date,
                available_weekday=random.choice(weekdays_available),
                available_from_time=available_from_time,
                available_to_time=available_to_time,
                slot_duration_minutes=random.choice(SLOT_DURATION_LIST),
                pause_minutes=random.choice(PAUSE_DURATION_LIST)
            )
            db.session.add(availability)
            db.session.commit()
        except Exception as e:
            current_app.logger.error("Error inserting availability: %s", e)
            db.session.rollback()
            continue

def insert_lab_closures(numberof_lab_closures=1):
    
    try:
        availabilites = Availability.query.all()
    except Exception as e:  
        current_app.logger.error("Error retrieving availabilities: %s", e)
        return
    
    while len(LaboratoryClosure.query.all()) < numberof_lab_closures:

        try:
            availability = random.choice(availabilites)

            start_datetime=generate_random_datetime(availability.available_from_date, availability.available_to_date)
            end_datetime=generate_random_datetime(start_datetime.date(), availability.available_to_date)

            closure = LaboratoryClosure(
                closure_id=uuid.uuid4(),
                laboratory_id=availability.laboratory_id,
                start_datetime=start_datetime,
                end_datetime=end_datetime
            )
            db.session.add(closure)
            db.session.commit()
        except Exception as e:
            current_app.logger.error("Error inserting laboratory closure: %s", e)
            db.session.rollback()
            continue

def insert_operator_absences(numberof_operator_absences=1):

    try:
        availabilities = Availability.query.all()
    except Exception as e:
        current_app.logger.error("Error retrieving availabilities: %s", e)
        return
    
    for i in range(numberof_operator_absences):

        try:
            availability = random.choice(availabilities)

            start_datetime=generate_random_datetime(availability.available_from_date, availability.available_to_date)
            end_datetime=generate_random_datetime(start_datetime.date(), availability.available_to_date)

            absence = OperatorAbsence(
                absence_id=uuid.uuid4(),
                operator_id=availability.operator_id,
                start_datetime=start_datetime,
                end_datetime=end_datetime
            )
            db.session.add(absence)
            db.session.commit()
        except Exception as e:
            current_app.logger.error("Error inserting operator absence: %s", e)
            db.session.rollback()
            continue
    
def insert_appointments(numberof_appointments=1):
    
    current_app.logger.info("Inserting appointments")

    try:
        availabilies = Availability.query.all()
    except Exception as e:
        current_app.logger.error("Error retrieving availabilities: %s", e)
        return
    empty_availabilities = []

    # cicla fino al numero di appuntamenti richiesti o fino a quando non ci sono più disponibilità
    while len(Appointment.query.all()) < numberof_appointments and len(empty_availabilities) < len(availabilies):
        
        availabilies_with_slots = [availability for availability in availabilies if availability.availability_id not in empty_availabilities]
        for j in range(len(availabilies_with_slots)):

            try:
                # seleziona una disponibilità e filtra appuntamenti, chiusure del laboratorio e assenze dell'operatore
                availability = availabilies_with_slots[j]
                laboratory_closures = LaboratoryClosure.query.filter_by(laboratory_id=availability.laboratory_id).all()
                operator_absences = OperatorAbsence.query.filter_by(operator_id=availability.operator_id).all()
                appointments = Appointment.query.filter_by(availability_id=availability.availability_id).all()

                datetime_from_filter = datetime.combine(availability.available_from_date, time(0, 0))
                date_to_filter = datetime.combine(availability.available_to_date, time(23, 59))
                groupd_slots = generate_available_slots([availability],datetime_from_filter,date_to_filter,laboratory_closures,operator_absences,appointments)

                if not groupd_slots:
                    empty_availabilities.append(availability.availability_id)
                    continue

                appointment_date = random.choice(list(groupd_slots.keys()))
                if len(groupd_slots[appointment_date]) == 0:
                    continue 

                slot = random.choice(groupd_slots[appointment_date])

                total_slot_count = sum(len(groupd_slots[d]) for d in groupd_slots)
                total_appointment_count = len(appointments)
                current_app.logger.debug("Generated %i appointments, %i remaining", total_appointment_count, total_slot_count)

                patient_id = random.choice([patient.patient_id for patient in Patient.query.all()])
                account_id = Patient.query.get(patient_id).account_id

                appointment = Appointment(
                    appointment_id=uuid.uuid4(),
                    availability_id=slot["availability_id"],
                    appointment_date=appointment_date,
                    appointment_time_start=datetime.strptime(slot["availability_slot_start"], "%H:%M").time(),
                    appointment_time_end=datetime.strptime(slot["availability_slot_end"], "%H:%M").time(),
                    account_id=account_id,
                    patient_id=patient_id
                )

                db.session.add(appointment)
                db.session.commit()

            except Exception as e:
                current_app.logger.error("Error inserting appointment: %s", e)
                db.session.rollback()
                continue

def test_generated_appointments():
    
    # Recupera tutte le disponibilità
    availabilities = Availability.query.all()

    # Generazione di tutti gli slot possibili
    grouped_slots_without_filter = generate_available_slots(availabilities)
    
    current_app.logger.debug("Generated %s slots", sum(len(slots) for slots in grouped_slots_without_filter.values()))
    
    # Estrai i dati sul db
    appointments = Appointment.query.all()

    for appointment in appointments:
        
        availability = Availability.query.get(appointment.availability_id)
        laboratory_closures = LaboratoryClosure.query.filter_by(laboratory_id=availability.laboratory_id).all()
        operator_absences = OperatorAbsence.query.filter_by(operator_id=availability.operator_id).all()

        slot_datime_start = datetime.combine(appointment.appointment_date,appointment.appointment_time_start)
        slot_datime_end = datetime.combine(appointment.appointment_date,appointment.appointment_time_end)
        availability_start = datetime.combine(availability.available_from_date ,availability.available_from_time)
        availability_end = datetime.combine(availability.available_to_date ,availability.available_to_time)

        slot_found = any(
            slot.get("availability_date") == appointment.appointment_date.isoformat() and
            slot.get("availability_slot_start") == appointment.appointment_time_start.strftime("%H:%M") and
            slot.get("availability_slot_end") == appointment.appointment_time_end.strftime("%H:%M")
            for slot in grouped_slots_without_filter.get(appointment.appointment_date.isoformat(), [])
        )

        try:
            # Verifica che lo slot sia contenuto nell'intervallo di disponibilità
            assert availability_start <= slot_datime_start and slot_datime_end <= availability_end, \
                f"appointment_id {appointment.appointment_id} from {slot_datime_start} to {slot_datime_end} overlap availability_id {availability.availability_id} from {availability_start} to {availability_end}"
            
            # Verifica che le deate dello slot siano corrette
            assert slot_datime_start != slot_datime_end, f"appointment_id {appointment.appointment_id} slot duration is zero"
            assert slot_datime_start < slot_datime_end, f"appointment_id {appointment.appointment_id} slot start is after slot end"
            
            # Verifica che lo slot non sia in sovrapposizione a chiusure del laboratorio o assenze dell'operatore
            if laboratory_closures:
                for closure in laboratory_closures:
                    assert slot_datime_end <= closure.start_datetime or slot_datime_start >= closure.end_datetime, \
                    f"appointment_id {appointment.appointment_id} overlap laboratory_closure_id {closure.closure_id}"
            
            # Verifica che lo slot non sia in sovrapposizione a chiusure del laboratorio o assenze dell'operatore
            if operator_absences:        
                for absence in operator_absences:
                    assert slot_datime_end <= absence.start_datetime or slot_datime_start >= absence.end_datetime, \
                           f"appointment_id {appointment.appointment_id} overlap operator_absence_id {absence.absence_id}"
            
            # Verifica che lo slot sia stato generato correttamente
            assert slot_found, f"appointment_id {appointment.appointment_id} failed consistency check"
        
        except Exception as e:
            current_app.logger.error("Error testing slot generator: %s", e)
            return False
    
    current_app.logger.debug("Test test_slot_generator passed.")
    return appointments

def insert_demo_data():
    # rispettare gli step di inserimento per evitare violazioni di chiave esterna
    insert_patients_operators(10, 10)
    insert_laboratories(10)
    insert_exam_types(10)
    insert_availabilities(50)
    insert_lab_closures(20)
    insert_operator_absences(20)
    insert_appointments(0)