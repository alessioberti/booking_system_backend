from flask import current_app
from app.models.model import db, Account, Location, Patient, Availability, Operator, Service, LocationClosure, OperatorAbsence, Appointment
from app.functions import generate_available_slots
import uuid
from datetime import date, time, datetime, timedelta
import random
from werkzeug.security import generate_password_hash

NUMBER_OF_PATIENTS = 10
NUMBER_OF_OPERATORS = 10
NUMBER_OF_LOCATIONS = 10
NUMBER_OF_SERVICES = 15
NUMBER_OF_AVAILABILITIES = 10
NUMBER_OF_LAB_CLOSURES = 3
NUMBER_OF_OPERATOR_ABSENCES = 3
NUMBER_OF_APPOINTMENTS = 50

NUMBER_OF_TESTS = 1

def clear_all_tables():
    try:
        # cancella tutte le righe delle tabelle in ordine inverso per evitare violazioni di chiave esterna
        with db.session.begin_nested():
            Appointment.query.delete()
            OperatorAbsence.query.delete()
            LocationClosure.query.delete()
            Availability.query.delete()
            Service.query.delete()
            Operator.query.delete()
            Patient.query.delete()
            Location.query.delete()
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

import uuid
from datetime import datetime
import random
from flask import current_app

def insert_patients_operators(numberof_patients=1, numberof_operators=1):
    
    FIRST_NAME_LAST_NAME_DICT = {
        "Alessio": "Arancioni",
        "Davide": "Verdi",
        "Mauro": "Azzurri",
        "Roberto": "Rosa",
        "Maurizio": "Celesti",
        "Giovanni": "Verdi",
        "Giovanna": "Blu",
        "Milena": "Bianchi",
        "Antonio": "Neri",
        "Alessia": "Gialli",
        "Mirko": "Arancioni",
        "Maura": "Viola",
        "Roberta": "Marroni",
        "Fabio": "Neri",
        "Giuseppe": "Gialli",
        "Federica": "Rossi"
    }

    MAX_ACCOUNTS = len(FIRST_NAME_LAST_NAME_DICT)

    try:
        created_operators = 0
        created_patients = 0
        created_accounts = 0
        numberof_accounts = numberof_patients + numberof_operators

        for first_name, last_name in FIRST_NAME_LAST_NAME_DICT.items():
                if created_accounts >= numberof_accounts or created_accounts >= MAX_ACCOUNTS:
                    return 

                # Creazione account
                first_name = first_name
                account_uuid = uuid.uuid4()
                account = Account(
                    account_id=account_uuid,
                    username= f"{first_name.lower()}.{last_name.lower()}",
                    password_hash="hashed_password",
                    enabled=True,
                    is_operator= True if created_operators < numberof_operators else False
                )
                db.session.add(account)
                
                 # Creazione operatore
                if created_operators < numberof_operators:
                    operator_uuid = uuid.uuid4()
                    operator = Operator(
                        operator_id=operator_uuid,
                        account_id=account_uuid,
                        title="Dott.",
                        first_name=first_name,
                        last_name=last_name
                    )
                    db.session.add(operator)
                    created_operators += 1

                # Creazione paziente
                if created_patients < numberof_patients:
                    patient_uuid = uuid.uuid4()
                    patient = Patient(
                        patient_id=patient_uuid,
                        account_id=account_uuid,
                        is_default=True,
                        first_name=first_name,
                        last_name=last_name,
                        email=f"{first_name.lower()}.{last_name.lower()}@gmail.com",
                        tel_number="+391234567890",
                        fiscal_code="FISCALCODE123456",
                        birth_date=datetime(
                            random.randint(1950, 2000),
                            random.randint(1, 12),
                            random.randint(1, 28)
                        ),
                        anonimized=False
                    )
                    db.session.add(patient)
                    created_patients += 1

                created_accounts = created_operators + created_patients

    except Exception as e:
        current_app.logger.error("Error inserting patients and operators: %s", e)
        return

def insert_locations(numberof_locations=1):
    
    LOCATION_LIST = ["L'Acquila","Chieti","Pescara","Catanzaro","Firenze","Teramo","Bari","Palermo","Genova","Catania","Brescia","Cosenza","Taranto","Prato","Modena"]
    MAX_LOCATIONS = len(LOCATION_LIST)
    try:
        created_locations = 0
        while created_locations < numberof_locations and created_locations < MAX_LOCATIONS:
            lab_uuid = uuid.uuid4()
            lab_name = f"Laboratorio {random.choice(LOCATION_LIST)}"
            lab_address = f"Via {random.choice(LOCATION_LIST)} {random.randint(1, 100)}"
            lab_tel_number = "+391234567890"
            location = Location(
                location_id=lab_uuid,
                name=lab_name,
                address=lab_address,
                tel_number=lab_tel_number
            )
            db.session.add(location)
            created_locations += 1

    except Exception as e:
        current_app.logger.error("Error inserting locations: %s", e)
        return
    
def insert_services(numberof_services=1):

    SERVICE_NAME_LIST = ["Visita Oculistica", "Visita Otorinolaringoiatrica", "Visita Cardiologica", "Visita Dermatologica", "Visita Ginecologica", "Visita Ortopedica", "Visita Pediatria", "Visita Psicologica", "Visita Urologica", "Visita Neurologica", "Visita Endocrinologica"]
    MAX_SERVICES = len(SERVICE_NAME_LIST)
    try:
        
        created_services = 0
        for i in range(numberof_services):
            if created_services >= MAX_SERVICES:
                break
            
            service_uuid = uuid.uuid4()
            service_name = SERVICE_NAME_LIST[i]
            
            service = Service(
                service_id=service_uuid,
                name=service_name
                
                )
            db.session.add(service)
            created_services += 1
          
    except Exception as e:
        current_app.logger.error("Error inserting service types: %s", e)
        return
    
def insert_availabilities(numberof_availabilities=1):
    SLOT_DURATION_LIST = [15, 30, 45, 60]
    PAUSE_DURATION_LIST = [0, 5, 10, 15]
    AVAILABILITY_START_LIST = [time(8, 0), time(9, 0), time(10, 0), time(11, 0)]
    
    try:
        services = Service.query.all()
        locations = Location.query.all()
        operators = Operator.query.all()
        
        created_availabilities = 0
        
        while created_availabilities < numberof_availabilities:
            available_from_date = datetime.today()
            available_to_date = available_from_date + timedelta(days=random.randint(1, 30)) + timedelta(hours=random.randint(1, 23))
            available_from_time = random.choice(AVAILABILITY_START_LIST)
            available_to_time = (datetime.combine(date.today(), available_from_time) + timedelta(hours=random.randint(4, 10))).time()
            weekday_available = generate_random_datetime(available_from_date, available_to_date).weekday()
            
            availability = Availability(
                availability_id=uuid.uuid4(),
                service_id=random.choice(services).service_id,
                location_id=random.choice(locations).location_id,
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
            current_app.logger.warning("No availabilities available, skipping location closures generation.")
            return

        created_lab_closures = 0
        while created_lab_closures < numberof_lab_closures:
        
            availability = random.choice(availabilites)
            start_datetime= datetime.today()
            end_datetime= start_datetime + timedelta(days=random.randint(1, 3)) 
            closure = LocationClosure(
                closure_id=uuid.uuid4(),
                location_id=availability.location_id,
                start_datetime=start_datetime,
                end_datetime=end_datetime
            )
            
            db.session.add(closure)
            created_lab_closures += 1

    except Exception as e:
        current_app.logger.error("Error inserting location closures: %s", e)
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
            end_datetime= start_datetime + timedelta(days=random.randint(1, 3)) + timedelta(hours=random.randint(1, 23))

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

def insert_appointments(numberof_appointments=1, max_not_founds=10):
    try:
        
        patients = Patient.query.all()
        services = Service.query.all()
        
        if not patients or not services:
            current_app.logger.warning("No patients or services available, skipping appointments generation.")
            return
        
        created_appointments = 0
        not_found = 0
        datetime_from_filter = datetime.now()
        datetime_to_filter = datetime_from_filter + timedelta(days=random.randint(1, 31)) + timedelta(hours=random.randint(1, 23))

        # Genera appuntamenti finché non ne sono stati creati abbastanza o finché non si raggiunge il numero massimo di tentativi
    
        while created_appointments < numberof_appointments and not_found < max_not_founds:
            
            #service = random.choice(services)
            patient = random.choice(patients)
            
            grouped_slots = generate_available_slots(
                datetime_from_filter=datetime_from_filter,
                datetime_to_filter=datetime_to_filter,
                service_id=None,
                operator_id=None,
                location_id=None,
                exclude_location_closure_slots=True,
                exclude_operator_absence_slots=True,
                exclude_booked_slots=True
            )
            
            if not grouped_slots:
                not_found += 1
                continue
            
            all_dates = list(grouped_slots.keys())
            random_date_str = random.choice(all_dates)
            slots_in_that_date = grouped_slots[random_date_str]
            random_slot = random.choice(slots_in_that_date)

            appointment_date = datetime.strptime(random_slot["appointment_date"], "%Y-%m-%d").date()

            time_start = datetime.strptime(random_slot["appointment_time_start"], "%H:%M").time()
            time_end   = datetime.strptime(random_slot["appointment_time_end"],   "%H:%M").time()

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
    try:
        appointments = Appointment.query.all()

        # Generazione di tutti gli slot possibili
        availabilities = Availability.query.all()
        appointments = Appointment.query.all()



        if not availabilities:
            current_app.logger.error("No availabilities available, skipping test.")
            return False

        all_generable_slots = generate_available_slots(
            exclude_location_closure_slots=False,
            exclude_operator_absence_slots=False,
            exclude_booked_slots=False
        )

        available_slots = generate_available_slots(
            exclude_booked_slots=True,
            exclude_location_closure_slots=True,
            exclude_operator_absence_slots=True
        )

        if not all_generable_slots:
            current_app.logger.error("Error generating slots")
            return False

        for appointment in appointments:
            
            availability = Availability.query.get(appointment.availability_id)
            location_closures = LocationClosure.query.filter_by(location_id=availability.location_id).all()
            operator_absences = OperatorAbsence.query.filter_by(operator_id=availability.operator_id).all()

            slot_datime_start = datetime.combine(appointment.appointment_date,appointment.appointment_time_start)
            slot_datime_end = datetime.combine(appointment.appointment_date,appointment.appointment_time_end)
            availability_start = datetime.combine(availability.available_from_date ,availability.available_from_time)
            availability_end = datetime.combine(availability.available_to_date ,availability.available_to_time)


            # Verifica che lo slot sia contenuto nell'intervallo di disponibilità
            assert availability_start <= slot_datime_start and slot_datime_end <= availability_end, \
                f"appointment_id {appointment.appointment_id} from {slot_datime_start} to {slot_datime_end} overlap availability_id {availability.availability_id} from {availability_start} to {availability_end}"
            
            # Verifica che le deate dello slot siano corrette
            assert slot_datime_start != slot_datime_end, f"appointment_id {appointment.appointment_id} slot duration is zero"
            assert slot_datime_start < slot_datime_end, f"appointment_id {appointment.appointment_id} slot start is after slot end"
            
            # Verifica che lo slot non sia in sovrapposizione a chiusure del laboratorio o assenze dell'operatore
            if location_closures:
                for closure in location_closures:
                    assert slot_datime_end <= closure.start_datetime or slot_datime_start >= closure.end_datetime, \
                    f"appointment_id {appointment.appointment_id} overlap location_closure_id {closure.closure_id}"
            
            # Verifica che lo slot non sia in sovrapposizione a chiusure del laboratorio o assenze dell'operatore
            if operator_absences:        
                for absence in operator_absences:
                    assert slot_datime_end <= absence.start_datetime or slot_datime_start >= absence.end_datetime, \
                            f"appointment_id {appointment.appointment_id} overlap operator_absence_id {absence.absence_id}"
            
            # Verifica che lo slot sia stato generato correttamente
            is_slot_into_slots_without_filter = any(
                slot.get("appointment_date") == appointment.appointment_date.isoformat() and
                slot.get("appointment_time_start") == appointment.appointment_time_start.strftime("%H:%M") and
                slot.get("appointment_time_end") == appointment.appointment_time_end.strftime("%H:%M")
                for slot in all_generable_slots.get(appointment.appointment_date.isoformat(), [])
            )
            
            assert is_slot_into_slots_without_filter, f"appointment_id {appointment.appointment_id} failed consistency check with slot generator"

            # Verifica che l'appuntamento non sia presente tra gli slot disponibili
            is_bookable_slot_already_booked = any(
                slot.get("appointment_date") == appointment.appointment_date.isoformat() and
                slot.get("appointment_time_start") == appointment.appointment_time_start.strftime("%H:%M") and
                slot.get("appointment_time_end") == appointment.appointment_time_end.strftime("%H:%M") and
                slot.get("availability_id") == appointment.availability_id
                for slot in available_slots.get(appointment.appointment_date.isoformat(), [])
            )

            assert not is_bookable_slot_already_booked, f"appointment_id {appointment.appointment_id} failed consistency check with booked slots"       
    
    except Exception as e:
        current_app.logger.error("Error testing slot generator: %s", e)
        return False
    
    current_app.logger.info("Test test_slot_generator passed.")
    current_app.logger.info("Total generalble %s", sum(len(slots) for slots in all_generable_slots.values()))
    current_app.logger.info("Available slots %s", sum(len(slots) for slots in available_slots.values()))
    return True

def insert_demo_data():

    try:    
        clear_all_tables()
        # rispettare gli step di inserimento per evitare violazioni di chiave esterna
        with db.session.begin_nested():
            insert_patients_operators(NUMBER_OF_PATIENTS, NUMBER_OF_OPERATORS)
            insert_locations(NUMBER_OF_LOCATIONS)
            insert_services(NUMBER_OF_SERVICES)
            insert_availabilities(NUMBER_OF_AVAILABILITIES)
            insert_lab_closures(NUMBER_OF_LAB_CLOSURES)
            insert_operator_absences(NUMBER_OF_OPERATOR_ABSENCES)
            insert_appointments(NUMBER_OF_APPOINTMENTS, 200)

        db.session.commit()
    except Exception as e:
        current_app.logger.error("Error inserting demo data: %s", e)
        db.session.rollback()
        return
    finally:

        appointments = Appointment.query.all()
        
        current_app.logger.info("Demo data inserted successfully Totals:")
        current_app.logger.info("Patients: %s", len(Patient.query.all()))
        current_app.logger.info("Operators: %s", len(Operator.query.all()))
        current_app.logger.info("Locations: %s", len(Location.query.all()))
        current_app.logger.info("Services: %s", len(Service.query.all()))
        current_app.logger.info("Availabilities: %s", len(Availability.query.all()))
        current_app.logger.info("LabClosures: %s", len(LocationClosure.query.all()))
        current_app.logger.info("OperatorAbsences: %s", len(OperatorAbsence.query.all()))
        current_app.logger.info("Appointments: %s", len(appointments))

        db.session.close()

def insert_demo_data_with_tests(number_of_test = NUMBER_OF_TESTS):
    
    try:
        for i in range(number_of_test):
            current_app.logger.info(f"Test number {i} of {number_of_test}")
            insert_demo_data()
            if test_generated_appointments() == False:
                current_app.logger.error("Test failed")
                raise RuntimeError("Failed test slot generator") 
    except Exception as e:
        current_app.logger.error("Error inserting demo data with tests: %s", e)
        raise