from flask import current_app
from app.models.model import db, Account, Laboratory, Patient, Availability, Operator, ExamType, LaboratoryClosure, OperatorAbsence, Appointment
from app.models.generate_available_slots import generate_available_slots
import uuid
from datetime import date, time, datetime, timedelta
import random

def generate_random_datetime(min_date: date, max_date: date) -> datetime:
    delta_days = (max_date - min_date).days
    random_days = random.randint(0, delta_days)
    return datetime.combine(min_date + timedelta(days=random_days), datetime.min.time())

def clear_existing_data():
    try:
        db.session.query(Appointment).delete()
        db.session.query(Availability).delete()
        db.session.query(OperatorAbsence).delete()
        db.session.query(Operator).delete()
        db.session.query(ExamType).delete()
        db.session.query(LaboratoryClosure).delete()
        db.session.query(Laboratory).delete()
        db.session.query(Patient).delete()
        db.session.query(Account).delete()
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e

import uuid
import random
from datetime import date, time, datetime, timedelta
from app.models.model import db, Account, Patient, Laboratory, LaboratoryClosure, ExamType, Operator, OperatorAbsence, Availability, Appointment

def insert_demo_data(patients=10, laboratories=6, exam_types=5, operators=5, availabilities=20, lab_closures=5, operator_absences=5, appointments=10):
    
    CURRENT_YEAR = 2025

    first_names_list = ["Alessio","Davide","Mauro","Roberto","Maurizio","Giovanni","Giovanna","Milena","Antonio","Alessia","Mirko","Maura","Roberta","Fabio","Giuseppe","Federica"]
    last_names_list = ["Arancioni","Verdi","Azzurri","Rosa","Celesti","Verdi","Blu","Bianchi","Neri","Gialli","Arancioni","Viola","Marroni","Neri","Gialli","Rossi"]
    cities_list = ["L'Acquila","Chieti","Pescara","Catanzaro","Firenze","Teramo","Bari","Palermo","Genova","Catania","Brescia","Cosenza","Taranto","Prato","Modena"]
    exam_names = ["Visita Oculistica", "Visita Otorinolaringoiatrica", "Visita Cardiologica", "Visita Dermatologica", "Visita Ginecologica", "Visita Ortopedica", "Visita Pediatria", "Visita Psicologica", "Visita Urologica", "Visita Neurologica", "Visita Endocrinologica"]
    slot_durations = [15, 30, 45, 60]
    pause_durations = [0, 5, 10, 15]
    availability_start_times = [time(8, 0), time(9, 0), time(10, 0), time(11, 0)]

    # create array to check unique emails
    already_created_emails = []
    already_booked_slots = []

    for i in range(patients):

        try:    
            email = ""
            for j in range(len(first_names_list) * len(last_names_list)):
                first_name = random.choice(first_names_list)
                last_name = random.choice(last_names_list)
                email = f"{first_name.lower()}.{last_name.lower()}@gmail.com"
                if email not in already_created_emails:
                    already_created_emails.append(email)
                    break
                
            if email == "":
                current_app.logger.warning("Cannot generate unique email for patient skipping.")
                break

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

    for i in range(operators):

        try:
            email = ""
            for j in range(len(first_names_list) * len(last_names_list)):
                first_name = random.choice(first_names_list)
                last_name = random.choice(last_names_list)
                email = f"{first_name.lower()}.{last_name.lower()}@gmail.com"
                if email not in already_created_emails:
                    already_created_emails.append(email)
                    break
                
            if email == "":
                current_app.logger.warning("Cannot generate unique email for operator skipping.")
                break

            first_name = random.choice(first_names_list)
            last_name = random.choice(last_names_list)
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

    for i in range(laboratories):
        
        try:
            lab_uuid = uuid.uuid4()
            lab = Laboratory(
                laboratory_id=lab_uuid,
                name=f"Laboratorio {random.choice(cities_list)}",
                address=f"Via {random.choice(cities_list)} {random.randint(1, 100)}",
                tel_number="+391234567890"
            )
            db.session.add(lab)
            db.session.commit()
        except Exception as e:
            current_app.logger.error("Error inserting laboratory: %s", e)
            db.session.rollback()
            continue

    for i in range(exam_types):
        
        try:
            exam_mame = ""
            for j in range(len(exam_names)):
            
                exam_mame = random.choice(exam_names)
                if exam_mame not in [exam_type.name for exam_type in ExamType.query.all()]:
                    break
            if exam_mame == "":
                current_app.logger.warning("Cannot generate unique exam name skipping.")
                break
            
            exam_type = ExamType(
                exam_type_id=uuid.uuid4(),
                name = exam_mame,
                description="Description"
            )
            db.session.add(exam_type)
            db.session.commit()
        except Exception as e:
            current_app.logger.error("Error inserting exam type: %s", e)
            db.session.rollback()
            continue

    for i in range(availabilities):

        try:
            available_from_date=(generate_random_datetime(date(CURRENT_YEAR, 1, 1), date(CURRENT_YEAR, 12, 31))).date()
            available_to_date=(available_from_date + timedelta(days=30 * random.randint(1, 6)))
            available_from_time=random.choice(availability_start_times)
            available_to_time = (datetime.combine(available_from_date, available_from_time) + timedelta(hours=random.randint(4, 10))).time()

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
                slot_duration_minutes=random.choice(slot_durations),
                pause_minutes=random.choice(pause_durations)
            )
            db.session.add(availability)
            db.session.commit()
        except Exception as e:
            current_app.logger.error("Error inserting availability: %s", e)
            db.session.rollback()
            continue

    for i in range(lab_closures):

        try:
            availabilitiy = random.choice(Availability.query.all())

            start_datetime=generate_random_datetime(availabilitiy.available_from_date, availabilitiy.available_to_date)
            end_datetime=generate_random_datetime(start_datetime.date(), availabilitiy.available_to_date)

            closure = LaboratoryClosure(
                closure_id=uuid.uuid4(),
                laboratory_id=availabilitiy.laboratory_id,
                start_datetime=start_datetime,
                end_datetime=end_datetime
            )
            db.session.add(closure)
            db.session.commit()
        except Exception as e:
            current_app.logger.error("Error inserting laboratory closure: %s", e)
            db.session.rollback()
            continue

    for i in range(operator_absences):

        try:
            availabilitiy = random.choice(Availability.query.all())

            start_datetime=generate_random_datetime(availabilitiy.available_from_date, availabilitiy.available_to_date)
            end_datetime=generate_random_datetime(start_datetime.date(), availabilitiy.available_to_date)

            absence = OperatorAbsence(
                absence_id=uuid.uuid4(),
                operator_id=availabilitiy.operator_id,
                start_datetime=start_datetime,
                end_datetime=end_datetime
            )
            db.session.add(absence)
            db.session.commit()
        except Exception as e:
            current_app.logger.error("Error inserting operator absence: %s", e)
            db.session.rollback()
            continue

    for i in range(appointments):
        
        try:
            availabilitiy = random.choice(Availability.query.all())

            available_from_date = availabilitiy.available_from_date + timedelta(days=(availabilitiy.available_weekday - available_from_date.weekday()) % 7)
            #current_app.logger.debug("Available from date: %s", available_from_date)
            available_to_date = availabilitiy.available_to_date - timedelta(days=(availabilitiy.available_weekday - available_to_date.weekday()) % 7)
            #current_app.logger.debug("Available to date: %s", available_to_date)

            random_date = ""
            for j in range((available_to_date - available_from_date).days + 1):

                random_date=generate_random_datetime(available_from_date, available_to_date).date()
                appointment_date = random_date + timedelta(days=(availabilitiy.available_weekday - random_date.weekday()) % 7)
                if available_from_date <= appointment_date <= available_to_date:
                    break
                else:
                    continue
                
            if random_date == "":
                current_app.logger.warning("Cannot generate unique date for appointment skipping.")
                break

            #current_app.logger.debug("Random date: %s", random_date)
            #current_app.logger.debug("Appointment date: %s", appointment_date)
            #current_app.logger.debug("Appointment date: %s", appointment_date)

            datetime_from_filter = datetime.combine(appointment_date, time(0, 0))
            datetime_to_filter = datetime.combine(appointment_date, time(23, 59))
            current_app.logger.debug("datetime_from_filter=%s, datetime_to_filter=%s", datetime_from_filter, datetime_to_filter)

            grouped_slots = generate_available_slots([availabilitiy], datetime_from_filter, datetime_to_filter)
            slots = grouped_slots[appointment_date.isoformat()]
            current_app.logger.debug("Slots for date %s: %s", appointment_date.isoformat(), grouped_slots.keys())
            slot = ""

            for j in range(len(slots)):
                slot = random.choice(slots)
                if slot not in already_booked_slots:
                    already_booked_slots.append(slot)
                    break
                
            if slot == "":
                current_app.logger.warning("Cannot generate unique slot skipping.")
                break

            appointment = Appointment(
                appointment_id=uuid.uuid4(),
                patient_id=random.choice(Patient.query.all()).patient_id,
                availability_id=availabilitiy.availability_id,
                appointment_date=appointment_date,
                appointment_time_start=datetime.strptime(slot["availability_slot_start"], "%H:%M").time(),
                appointment_time_end=datetime.strptime(slot["availability_slot_end"], "%H:%M").time(),
            )
            db.session.add(appointment)
            db.session.commit()
        except Exception as e:
            current_app.logger.error("Error inserting appointment: %s", e)
            db.session.rollback()
            continue
    
    current_app.logger.info("Demo data inserted successfully.")

def test_slot_generator(number_of_random_tests=10):
    # Recupera tutte le disponibilità
    availabilities = Availability.query.all()
    assert len(availabilities) > 0, "Nessuna disponibilità trovata."
    current_app.logger.debug("Count of availabilities: %d", len(availabilities))

    # Genera una baseline di slot senza filtri
    slots_without_filter = generate_available_slots(availabilities)
    baseline_count = sum(len(slots) for slots in slots_without_filter.values())
    assert baseline_count > 0, "Nessuno slot generato senza filtri."
    current_app.logger.debug("Count of slots without filter: %d", baseline_count)

    # Estrai la data minima e massima dalle disponibilità
    min_date = min(avail.available_from_date for avail in availabilities)
    max_date = max(avail.available_to_date for avail in availabilities)
    
    for i in range(number_of_random_tests):
        # Seleziona una data casuale valida
        random_date = generate_random_datetime(min_date, max_date).date()
        datetime_from_filter = datetime.combine(random_date, time(0, 0))
        datetime_to_filter = datetime.combine(random_date, time(23, 59))
        current_app.logger.debug("START Test %d: datetime_from_filter=%s, datetime_to_filter=%s", 
                                   i, datetime_from_filter, datetime_to_filter)

        # Genera gli slot con filtri per quella data
        grouped_slots = generate_available_slots(
            availabilities,
            datetime_from_filter=datetime_from_filter,
            datetime_to_filter=datetime_to_filter,
            laboratory_closures=LaboratoryClosure.query.all(),
            operator_absences=OperatorAbsence.query.all(),
            appointments=Appointment.query.all()
        )

        # I gruppi sono indicizzati per data in formato ISO
        key = random_date.isoformat()
        current_app.logger.debug("For date %s, generated slots: %s", key, grouped_slots.get(key))
        if key not in grouped_slots or not grouped_slots[key]:
            current_app.logger.warning("No slots generated for date %s, skipping iteration.", key)
            continue

        for slot in grouped_slots[key]:
            # Converti gli orari dello slot in datetime usando la data di base (key)
            slot_start = datetime.strptime(slot["availability_slot_start"], "%H:%M").time()
            slot_end = datetime.strptime(slot["availability_slot_end"], "%H:%M").time()

            current_app.logger.debug("Slot: start=%s, end=%s", slot_start, slot_end)

            # Verifica che lo slot sia compreso nell'intervallo impostato
            assert slot_start >= datetime_from_filter and slot_end <= datetime_to_filter, \
                f"Slot {slot} non compreso nel range {datetime_from_filter} - {datetime_to_filter}"

            # Verifica che lo slot non si sovrapponga a chiusure di laboratorio
            for closure in LaboratoryClosure.query.all():
                assert slot_end <= closure.start_datetime or slot_start >= closure.end_datetime, \
                    f"Slot {slot} confligge con closure {closure}"

            # Verifica che lo slot non si sovrapponga a assenze dell'operatore
            for absence in OperatorAbsence.query.all():
                assert slot_end <= absence.start_datetime or slot_start >= absence.end_datetime, \
                    f"Slot {slot} confligge con absence {absence}"

            # Verifica che lo slot non entri in conflitto con un appuntamento esistente
            for appointment in Appointment.query.all():
                appointment_start = datetime.combine(appointment.appointment_date, appointment.appointment_time_start)
                assert slot_start != appointment_start, \
                    f"Slot {slot} confligge con appointment a {appointment_start}"

            # Consistenza: lo slot generato con i filtri deve apparire anche nella baseline
            found = False
            if key in slots_without_filter:
                for baseline_slot in slots_without_filter[key]:
                    if baseline_slot == slot:
                        found = True
                        break
            assert found, f"Slot {slot} non trovato nei baseline slots per la data {key}"

    current_app.logger.debug("Test test_slot_generator passed.")
    return grouped_slots

