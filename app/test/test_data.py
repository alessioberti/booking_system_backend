from flask import current_app
from app.models.model import db, Account, Laboratory, Patient, Availability, Operator, ExamType, LaboratoryClosure, OperatorAbsence, Appointment
from app.functions import generate_available_slots
import uuid
from datetime import date, time, datetime, timedelta
import random

def clear_all_tables():
    try:
        # cancella tutte le righe delle tabelle in ordine inverso per evitare violazioni di chiave esterna
        with db.session.begin_nested():
            Appointment.query.delete()
            OperatorAbsence.query.delete()
            LaboratoryClosure.query.delete()
            Availability.query.delete()
            ExamType.query.delete()
            Operator.query.delete()
            Patient.query.delete()
            Laboratory.query.delete()
            Account.query.delete()
        db.session.commit()
    except Exception as e:
        current_app.logger.error("Error truncating tables: %s", e)
        return
    finally:
        db.session.close()

def generate_random_datetime(min_date: date, max_date: date) -> datetime:
    delta_days = (max_date - min_date).days
    random_days = random.randint(0, delta_days)
    random_time = time(random.randint(0, 23), random.randint(0, 59))
    return datetime.combine(min_date + timedelta(days=random_days), random_time)

def insert_patients_operators(numberof_patients=1, numberof_operators=1):
    FIRST_NAME_LIST = ["Alessio","Davide","Mauro","Roberto","Maurizio","Giovanni","Giovanna","Milena","Antonio","Alessia","Mirko","Maura","Roberta","Fabio","Giuseppe","Federica"]
    LAST_NAME_LIST = ["Arancioni","Verdi","Azzurri","Rosa","Celesti","Verdi","Blu","Bianchi","Neri","Gialli","Arancioni","Viola","Marroni","Neri","Gialli","Rossi"]

    try:
        
        already_created_emails = []

        for i in range(numberof_patients):
        
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

        for i in range(numberof_operators):
        
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
    except Exception as e:
        current_app.logger.error("Error inserting patients and operators: %s", e)
        return
        
def insert_laboratories(numberof_laboratories=1):
    
    LOCATION_LIST = ["L'Acquila","Chieti","Pescara","Catanzaro","Firenze","Teramo","Bari","Palermo","Genova","Catania","Brescia","Cosenza","Taranto","Prato","Modena"]

    try:
      
        for i in range(numberof_laboratories):

            lab_uuid = uuid.uuid4()
            lab = Laboratory(
                laboratory_id=lab_uuid,
                name=f"Laboratorio {random.choice(LOCATION_LIST)}",
                address=f"Via {random.choice(LOCATION_LIST)} {random.randint(1, 100)}",
                tel_number="+391234567890"
            )
            
            db.session.add(lab)

    except Exception as e:
        current_app.logger.error("Error inserting laboratories: %s", e)
        return
    
def insert_exam_types(numberof_exam_types=1):

    EXAM_NAME_LIST = ["Visita Oculistica", "Visita Otorinolaringoiatrica", "Visita Cardiologica", "Visita Dermatologica", "Visita Ginecologica", "Visita Ortopedica", "Visita Pediatria", "Visita Psicologica", "Visita Urologica", "Visita Neurologica", "Visita Endocrinologica"]
    
    try:
        
        while len(ExamType.query.all()) < numberof_exam_types:

            if len(ExamType.query.all()) == len(EXAM_NAME_LIST):
                break
            
            for exam_mame in EXAM_NAME_LIST:
            
                exam_type = ExamType(
                    exam_type_id=uuid.uuid4(),
                    name = exam_mame,
                    description="Descrizione esame " + exam_mame
                )
                
                db.session.add(exam_type)

    except Exception as e:
        current_app.logger.error("Error inserting exam types: %s", e)
        return

def insert_availabilities(numberof_availabilities=1):
    SLOT_DURATION_LIST = [15, 30, 45, 60]
    PAUSE_DURATION_LIST = [0, 5, 10, 15]
    AVAILABILITY_START_LIST = [time(8, 0), time(9, 0), time(10, 0), time(11, 0)]
    
    try:
        exam_types = ExamType.query.all()
        laboratories = Laboratory.query.all()
        operators = Operator.query.all()
        
        created_availabilities = 0
        
        while created_availabilities < numberof_availabilities:
            available_from_date = datetime.today()
            available_to_date = available_from_date + timedelta(days=random.randint(0, 30)) + timedelta(hours=random.randint(0, 23))
            available_from_time = random.choice(AVAILABILITY_START_LIST)
            available_to_time = (datetime.combine(date.today(), available_from_time) + timedelta(hours=random.randint(4, 10))).time()
            weekday_available = generate_random_datetime(available_from_date, available_to_date).weekday()
            
            availability = Availability(
                availability_id=uuid.uuid4(),
                exam_type_id=random.choice(exam_types).exam_type_id,
                laboratory_id=random.choice(laboratories).laboratory_id,
                operator_id=random.choice(operators).operator_id,
                available_from_date=available_from_date,
                available_to_date=available_to_date,
                available_weekday=weekday_available,
                available_from_time=available_from_time,
                available_to_time=available_to_time,
                slot_duration_minutes=random.choice(SLOT_DURATION_LIST),
                pause_minutes=random.choice(PAUSE_DURATION_LIST)
            )
            
            db.session.add(availability)
            created_availabilities += 1
        
    except Exception as e:
        current_app.logger.error("Error inserting availabilities: %s", e)
        return

def insert_lab_closures(numberof_lab_closures=1):
    
    try:
    
        availabilites = Availability.query.all()
        if not availabilites:
            current_app.logger.warning("No availabilities available, skipping laboratory closures generation.")
            return

        created_lab_closures = 0
        while created_lab_closures < numberof_lab_closures:
        
            availability = random.choice(availabilites)
            start_datetime= datetime.today()
            end_datetime= start_datetime + timedelta(days=random.randint(0, 3)) 
            closure = LaboratoryClosure(
                closure_id=uuid.uuid4(),
                laboratory_id=availability.laboratory_id,
                start_datetime=start_datetime,
                end_datetime=end_datetime
            )
            
            db.session.add(closure)
            created_lab_closures += 1
    except Exception as e:
        current_app.logger.error("Error inserting laboratory closures: %s", e)
        return
        
def insert_operator_absences(numberof_operator_absences=1):

    try:
        
        availabilities = Availability.query.all()
        if not availabilities:
            current_app.logger.warning("No availabilities available, skipping operator absences generation.")
            return
        
        for i in range(numberof_operator_absences):
        
            availability = random.choice(availabilities)

            start_datetime=datetime.today()
            end_datetime= start_datetime + timedelta(days=random.randint(0, 3)) + timedelta(hours=random.randint(0, 23))

            absence = OperatorAbsence(
                absence_id=uuid.uuid4(),
                operator_id=availability.operator_id,
                start_datetime=start_datetime,
                end_datetime=end_datetime
            )
            
            db.session.add(absence)

    except Exception as e:
        current_app.logger.error("Error inserting operator absences: %s", e)
        return

def insert_appointments(numberof_appointments=1, not_found_retry=10):
    try:
        
        patients = Patient.query.all()
        exam_types = ExamType.query.all()
        
        if not patients or not exam_types:
            current_app.logger.warning("No patients or exam_types available, skipping appointments generation.")
            return
        
        created_appointments = 0
        not_found = 0
        datetime_from_filter = datetime.now()
        datetime_to_filter = datetime_from_filter + timedelta(days=random.randint(0, 31)) + timedelta(hours=random.randint(0, 23))
        
        while created_appointments < numberof_appointments and not_found < not_found_retry:
            
            exam_type = random.choice(exam_types)
            patient = random.choice(patients)
            
            grouped_slots = generate_available_slots(
                datetime_from_filter=datetime_from_filter,
                datetime_to_filter=datetime_to_filter,
                exam_type_id=exam_type.exam_type_id,
                operator_id=None,
                laboratory_id=None,
                exclude_laboratory_closoure_slots=True,
                exclude_operator_abesence_slots=True,
                exclude_booked_slots=True
            )
            
            if not grouped_slots:
                not_found += 1
                continue
            
            all_dates = list(grouped_slots.keys())
            random_date_str = random.choice(all_dates)
            slots_in_that_date = grouped_slots[random_date_str]
            random_slot = random.choice(slots_in_that_date)

            appointment_date = datetime.fromisoformat(random_slot["availability_date"]).date()

            time_start = datetime.strptime(random_slot["availability_slot_start"], "%H:%M").time()
            time_end   = datetime.strptime(random_slot["availability_slot_end"],   "%H:%M").time()

            appointment = Appointment(
                appointment_id=uuid.uuid4(),
                availability_id=random_slot["availability_id"],
                appointment_date=appointment_date,
                appointment_time_start=time_start,
                appointment_time_end=time_end,
                account_id=patient.account_id,
                patient_id=patient.patient_id
            )
            db.session.add(appointment)
            created_appointments += 1
        
    except Exception as e:
        current_app.logger.error("Error inserting appointments: %s", e)
        return

def test_generated_appointments():

    # Generazione di tutti gli slot possibili
    availabilities = Availability.query.all()
    if not availabilities:
        current_app.logger.error("No availabilities available, skipping test.")
        return False
    
    grouped_slots_without_filter = generate_available_slots()
    
    if not grouped_slots_without_filter:
        current_app.logger.error("Error generating slots")
        return False

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
            is_slot_into_slots_without_filter = any(
                slot.get("availability_date") == appointment.appointment_date.isoformat() and
                slot.get("availability_slot_start") == appointment.appointment_time_start.strftime("%H:%M") and
                slot.get("availability_slot_end") == appointment.appointment_time_end.strftime("%H:%M")
                for slot in grouped_slots_without_filter.get(appointment.appointment_date.isoformat(), [])
            )
            try:
                
                assert is_slot_into_slots_without_filter, f"appointment_id {appointment.appointment_id} failed consistency check with slot generator"
            
            except Exception:
                
                current_app.logger.error("Error consistency check with slot id %s %s %s", appointment.appointment_id, appointment.appointment_date, appointment.appointment_time_start)
                current_app.logger.error("Generated slots for the same date:")
                for slot in grouped_slots_without_filter.get(appointment.appointment_date.isoformat(), []):
                    current_app.logger.error("Slot: %s %s %s", slot.get("availability_date"), slot.get("availability_slot_start"), slot.get("availability_slot_end"))
        
        except Exception as e:
            current_app.logger.error("Error testing slot generator: %s", e)
            return False
    
    current_app.logger.debug("Test test_slot_generator passed.")
    return True

def insert_demo_data():

    try:    
        clear_all_tables()
        # rispettare gli step di inserimento per evitare violazioni di chiave esterna
        with db.session.begin_nested():
            insert_patients_operators(10, 10)
            insert_laboratories(10)
            insert_exam_types(10)
            insert_availabilities(50)
            insert_lab_closures(20)
            insert_operator_absences(20)
            insert_appointments(500, 1000)
        db.session.commit()
    except Exception as e:
        current_app.logger.error("Error inserting demo data: %s", e)
        db.session.rollback()
        return
    finally:
        current_app.logger.info("Demo data inserted successfully Totals:")
        current_app.logger.info("Patients: %s", len(Patient.query.all()))
        current_app.logger.info("Operators: %s", len(Operator.query.all()))
        current_app.logger.info("Laboratories: %s", len(Laboratory.query.all()))
        current_app.logger.info("ExamTypes: %s", len(ExamType.query.all()))
        current_app.logger.info("Availabilities: %s", len(Availability.query.all()))
        current_app.logger.info("LabClosures: %s", len(LaboratoryClosure.query.all()))
        current_app.logger.info("OperatorAbsences: %s", len(OperatorAbsence.query.all()))
        current_app.logger.info("Appointments: %s", len(Appointment.query.all()))

        db.session.close()

def insert_demo_data_with_tests(number_of_test = 1):
    
    try:
        for i in range(number_of_test):
            current_app.logger.info(f"Test number {i} of {number_of_test}")
            insert_demo_data()
            if test_generated_appointments() == False:
                current_app.logger.error("Test failed")
                return
    except Exception as e:
        current_app.logger.error("Error inserting demo data with tests: %s", e)
        return