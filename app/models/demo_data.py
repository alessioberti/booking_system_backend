import uuid
from app import db
from app.models.model import Account, Laboratory, ExamType, Operator, Availability, OperatorAbsence, LaboratoryClosure, Patient, Appointment
from datetime import date, time
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
        print("Dati esistenti rimossi con successo.")
    except Exception as e:
        db.session.rollback()
        print(f"Errore durante la rimozione dei dati: {e}")


def insert_demo_data():
    try:
        account_uuids = {
            "marco_rossi": uuid.uuid4(),
            "giulia_verdi": uuid.uuid4(),
            "luca_bianchi": uuid.uuid4(),
            "sara_neri": uuid.uuid4()
        }
        accounts = [
            Account(
                account_id=account_uuids["marco_rossi"],
                password_hash="hashed_password1",
                email="marco.rossi@example.com",
                enabled=True,
                failed_login_count=0,
                is_operator=True,
                is_admin=False,
            ),
            Account(
                account_id=account_uuids["giulia_verdi"],
                password_hash="hashed_password2",
                email="giulia.verdi@example.com",
                enabled=True,
                failed_login_count=0,
                is_operator=False,
                is_admin=True,
            ),
            Account(
                account_id=account_uuids["luca_bianchi"],
                password_hash="hashed_password3",
                email="luca.bianchi@example.com",
                enabled=True,
                failed_login_count=0,
                is_operator=True,
                is_admin=False,
            ),
            Account(
                account_id=account_uuids["sara_neri"],
                password_hash="hashed_password4",
                email="sara.neri@example.com",
                enabled=True,
                failed_login_count=0,
                is_operator=True,
                is_admin=False,
            ),
        ]
        db.session.add_all(accounts)
        laboratory_uuids = {
            "milano": uuid.uuid4(),
            "torino": uuid.uuid4(),
            "roma": uuid.uuid4(),
            "napoli": uuid.uuid4()
        }
        laboratories = [
            Laboratory(
                laboratory_id=laboratory_uuids["milano"],
                name="Laboratorio Sanità Milano",
                address="Via Roma 10, Milano",
                contact_info="info.milano@laboratori.it",
            ),
            Laboratory(
                laboratory_id=laboratory_uuids["torino"],
                name="Centro Analisi Torino",
                address="Corso Francia 25, Torino",
                contact_info="info.torino@laboratori.it",
            ),
            Laboratory(
                laboratory_id=laboratory_uuids["roma"],
                name="Clinica Roma",
                address="Via Nazionale 15, Roma",
                contact_info="info.roma@laboratori.it",
            ),
            Laboratory(
                laboratory_id=laboratory_uuids["napoli"],
                name="Laboratorio Napoli",
                address="Piazza Garibaldi 20, Napoli",
                contact_info="info.napoli@laboratori.it",
            ),
        ]
        db.session.add_all(laboratories)

        exam_type_uuids = {
            "esame_sangue": uuid.uuid4(),
            "tampone": uuid.uuid4(),
            "ecg": uuid.uuid4(),
            "radiografia": uuid.uuid4()
        }
        exam_types = [
            ExamType(
                exam_type_id=exam_type_uuids["esame_sangue"],
                name="Esame del Sangue",
                description="Analisi ematica completa",
            ),
            ExamType(
                exam_type_id=exam_type_uuids["tampone"],
                name="Tampone Molecolare",
                description="Test molecolare per COVID-19",
            ),
            ExamType(
                exam_type_id=exam_type_uuids["ecg"],
                name="ECG",
                description="Elettrocardiogramma",
            ),
            ExamType(
                exam_type_id=exam_type_uuids["radiografia"],
                name="Radiografia",
                description="Radiografia standard",
            ),
        ]
        db.session.add_all(exam_types)
        operator_uuids = {
            "francesca_conti": uuid.uuid4(),
            "alessandro_ricci": uuid.uuid4(),
            "luca_bianchi": uuid.uuid4(),
            "sara_neri": uuid.uuid4()
        }
        operators = [
            Operator(
                operator_id=operator_uuids["francesca_conti"],
                name="Dott.ssa Francesca Conti",
                account_id=account_uuids["marco_rossi"],
            ),
            Operator(
                operator_id=operator_uuids["alessandro_ricci"],
                name="Specialista Alessandro Ricci",
                account_id=account_uuids["giulia_verdi"],
            ),
            Operator(
                operator_id=operator_uuids["luca_bianchi"],
                name="Dott. Luca Bianchi",
                account_id=account_uuids["luca_bianchi"],
            ),
            Operator(
                operator_id=operator_uuids["sara_neri"],
                name="Specialista Sara Neri",
                account_id=account_uuids["sara_neri"],
            ),
        ]
        db.session.add_all(operators)

        availability_uuids = {
            "francesca_lunedi": uuid.uuid4(),
            "alessandro_mercoledi": uuid.uuid4(),
            "luca_venerdi": uuid.uuid4(),
            "sara_martedi": uuid.uuid4(),
            "francesca_giovedi": uuid.uuid4()
        }

        availabilities = [
            Availability(
                availability_id=availability_uuids["francesca_lunedi"],
                operator_id=operator_uuids["francesca_conti"],
                laboratory_id=laboratory_uuids["milano"],
                exam_type_id=exam_type_uuids["esame_sangue"],
                available_from_date=date(2025, 1, 22),
                available_to_date=date(2025, 6, 30),
                available_from_time=time(9, 0),
                available_to_time=time(17, 0),
                available_weekday=1,
                slot_duration_minutes=30,
                pause_minutes=10,
                enabled=True,
            ),
            Availability(
                availability_id=availability_uuids["alessandro_mercoledi"],
                operator_id=operator_uuids["alessandro_ricci"],
                laboratory_id=laboratory_uuids["torino"],
                exam_type_id=exam_type_uuids["tampone"],
                available_from_date=date(2025, 1, 22),
                available_to_date=date(2025, 12, 31),
                available_from_time=time(8, 30),
                available_to_time=time(12, 30),
                available_weekday=3,
                slot_duration_minutes=20,
                pause_minutes=5,
                enabled=True,
            ),
            Availability(
                availability_id=availability_uuids["luca_venerdi"],
                operator_id=operator_uuids["luca_bianchi"],
                laboratory_id=laboratory_uuids["roma"],
                exam_type_id=exam_type_uuids["ecg"],
                available_from_date=date(2025, 1, 22),
                available_to_date=date(2025, 6, 30),
                available_from_time=time(9, 0),
                available_to_time=time(13, 0),
                available_weekday=5,
                slot_duration_minutes=15,
                pause_minutes=5,
                enabled=True,
            ),
            Availability(
                availability_id=availability_uuids["sara_martedi"],
                operator_id=operator_uuids["sara_neri"],
                laboratory_id=laboratory_uuids["napoli"],
                exam_type_id=exam_type_uuids["radiografia"],
                available_from_date=date(2025, 1, 22),
                available_to_date=date(2025, 11, 30),
                available_from_time=time(10, 0),
                available_to_time=time(14, 0),
                available_weekday=2,
                slot_duration_minutes=25,
                pause_minutes=10,
                enabled=True,
            ),
            Availability(
                availability_id=availability_uuids["francesca_giovedi"],
                operator_id=operator_uuids["francesca_conti"],
                laboratory_id=laboratory_uuids["milano"],
                exam_type_id=exam_type_uuids["radiografia"],
                available_from_date=date(2025, 1, 22),
                available_to_date=date(2025, 6, 30),
                available_from_time=time(14, 0),
                available_to_time=time(18, 0),
                available_weekday=4,
                slot_duration_minutes=20,
                pause_minutes=5,
                enabled=True,
            ),
        ]
        db.session.add_all(availabilities)

        # Commit
        db.session.commit()
        print("Dati demo inseriti con successo.")
    except Exception as e:
        db.session.rollback()
        print(f"Errore durante la generazione dei dati demo: {e}")
