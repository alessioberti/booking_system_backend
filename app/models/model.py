import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text, Index
from app.extensions import db
from datetime import datetime
from flask import current_app
class Account(db.Model):
    __tablename__ = "account"

    account_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    username = db.Column(db.String(254), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)
    enabled = db.Column(db.Boolean, default=True, nullable=False)
    failed_login_count = db.Column(db.Integer, default=0)
    last_failed_login = db.Column(db.DateTime, nullable=True)
    last_success_login = db.Column(db.DateTime, nullable=True)
    is_operator = db.Column(db.Boolean, default=False, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    # Relazioni
    operator = db.relationship("Operator", back_populates="account")
    patient = db.relationship("Patient", back_populates="account")
    appointment = db.relationship("Appointment", back_populates="account")

    # Metodi

    # crea account e paziente di default
    def create_new(self, email,first_name,last_name,tel_number,fiscal_code,birth_date):
            
            db.session.add(self)
            # usa il flush per ottenere l'id dell'account
            db.session.flush()
            current_app.logger.info("Account created %s", self.account_id)

            # converti la data di nascita in date se presente
            birth_date_date = (datetime.fromisoformat(birth_date)).date() if birth_date else None
            
            default_patient = Patient(
                account_id=self.account_id,
                first_name=first_name,
                last_name=last_name,
                email=email,
                tel_number=tel_number,
                fiscal_code=fiscal_code,
                birth_date= birth_date_date,
                is_default=True # il primo paziente creato è il paziente di default
            )
            db.session.add(default_patient)

    def to_dict(self):
        return {
            "account_id": self.account_id,
            "username": self.username,
        }
    
     # anonimizza tutti i pazienti collegati all'account mantenendo solo l'id e dati per scopi statistici
    def anonimize(self):
        account_patients = Patient.query.filter_by(account_id=self.account_id).all()
        for patient in account_patients:
            patient.first_name = uuid.uuid4().hex
            patient.last_name = uuid.uuid4().hex
            patient.email = uuid.uuid4().hex
            patient.tel_number = None
            # anonimizza il codice fiscale se è lungo 16 caratteri altrimenti se è stato inserito un codice fiscale errato o un documento lo elimina
            if patient.fiscal_code and len(patient.fiscal_code) == 16:
                patient.fiscal_code = "XXXXXX" + patient.fiscal_code[6:]
            else:
                patient.fiscal_code = None
            patient.anonimized = True

        # anonimizza gli appuntamenti collegati all'account
        account_appointments = Appointment.query.filter_by(account_id=self.account_id).all()
        for appointment in account_appointments:
            appointment.info = None

        # anonimizza l'account
        self.enabled = False
        self.username = uuid.uuid4().hex
        self.password_hash = uuid.uuid4().hex
   
class Patient(db.Model):
    __tablename__ = "patient"

    patient_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    account_id = db.Column(UUID(as_uuid=True), db.ForeignKey("account.account_id"), nullable=False)
    is_default = db.Column(db.Boolean, default=False, nullable=False)
    first_name = db.Column(db.String(32), nullable=False)
    last_name = db.Column(db.String(32), nullable=False)
    email = db.Column(db.String(254), nullable=False)
    tel_number = db.Column(db.String(32) , nullable=True)
    fiscal_code = db.Column(db.String(32) , nullable=True)
    birth_date = db.Column(db.Date , nullable=True)
    anonimized = db.Column(db.Boolean, default=False, nullable=False)

    # Relazioni
    account = db.relationship("Account", back_populates="patient")
    appointment = db.relationship("Appointment", back_populates="patient")

    def to_dict(self):
        return {
            "patient_id": self.patient_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "tel_number": self.tel_number,
            "fiscal_code": self.fiscal_code,
            "birth_date": self.birth_date.isoformat() if self.birth_date else None,
            "is_default": self.is_default,
        }

    # Vincoli
    # evita più pazienti di default per account
    __table_args__ = (
        Index(
            "ix_account_default_patient",
            "account_id",
            unique=True,
            postgresql_where=text("is_default = true")
        ),
    )


class Location(db.Model):
    __tablename__ = "location"

    location_id = db.Column( UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(255), nullable=True)
    tel_number = db.Column(db.String(255), nullable=True)

    # Relazioni
    availability = db.relationship("Availability", back_populates="location")
    location_closure = db.relationship("LocationClosure", back_populates="location")

    # Metodi

    def to_dict(self):
        return {
            "location_id": self.location_id,
            "name": self.name,
        }

class LocationClosure(db.Model):
    __tablename__ = "location_closure"

    closure_id = db.Column( UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    location_id = db.Column( UUID(as_uuid=True), db.ForeignKey("location.location_id"), nullable=False)
    start_datetime = db.Column(db.DateTime, nullable=False)
    end_datetime = db.Column(db.DateTime, nullable=False)

    # Relationships

    location = db.relationship("Location", back_populates="location_closure")
    
    # Metodi 

class Service(db.Model):
    __tablename__ = "service"

    service_id = db.Column( UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    name = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.String, nullable=True)

     # Relationships
    availability = db.relationship("Availability", back_populates="service")

    # Metodi

    # restituisce un dizionario con i dati dell'esame e un flag per indicare se ci sono disponibilità attive
    def to_dict(self):
        return {
            "service_id": self.service_id,
            "name": self.name,
            "description": self.description,
            "has_enabled_availability": any(av.enabled for av in self.availability)
        }

class Operator(db.Model):
    __tablename__ = "operators"

    operator_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    account_id = db.Column(UUID(as_uuid=True), db.ForeignKey("account.account_id"), unique=True, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)

     # Relazioni
    account = db.relationship("Account", back_populates="operator")
    availability = db.relationship("Availability", back_populates="operator")
    operator_absence = db.relationship("OperatorAbsence", back_populates="operator")

    # Metodi
    def to_dict(self):
        return {
            "operator_id": self.operator_id,
            "name": f"{self.title} {self.first_name} {self.last_name}",
        }

class OperatorAbsence(db.Model):
    __tablename__ = "operator_absence"

    absence_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    operator_id = db.Column(UUID(as_uuid=True),db.ForeignKey("operators.operator_id"),nullable=False)
    start_datetime = db.Column(db.DateTime, nullable=False)
    end_datetime = db.Column(db.DateTime, nullable=False)

    # Relazioni
    operator = db.relationship("Operator", back_populates="operator_absence")

class Availability(db.Model):
    __tablename__ = "availability"

    availability_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False )
    service_id = db.Column(UUID(as_uuid=True),db.ForeignKey("service.service_id"),nullable=False)
    location_id = db.Column(UUID(as_uuid=True),db.ForeignKey("location.location_id"),nullable=False)
    operator_id = db.Column(UUID(as_uuid=True),db.ForeignKey("operators.operator_id"),nullable=False)
    available_from_date = db.Column(db.Date, nullable=False)
    available_to_date = db.Column(db.Date, nullable=False)
    available_from_time = db.Column(db.Time, nullable=False)
    available_to_time = db.Column(db.Time, nullable=False)
    available_weekday = db.Column(db.Integer, nullable=False)
    slot_duration_minutes = db.Column(db.Integer, nullable=False)
    pause_minutes = db.Column(db.Integer, nullable=False)
    enabled = db.Column(db.Boolean, default=True, nullable=False)

    #Relazioni

    location = db.relationship("Location", back_populates="availability")
    operator = db.relationship("Operator", back_populates="availability")
    service = db.relationship("Service", back_populates="availability")
    appointment = db.relationship("Appointment", back_populates="availability")
    
    # Metodi

class Appointment(db.Model):
    __tablename__ = "appointment"

    appointment_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    account_id = db.Column(UUID(as_uuid=True), db.ForeignKey("account.account_id"), nullable=False)
    patient_id = db.Column(UUID(as_uuid=True), db.ForeignKey("patient.patient_id"), nullable=False)
    availability_id = db.Column( UUID(as_uuid=True), db.ForeignKey("availability.availability_id"), nullable=False)
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time_start = db.Column(db.Time, nullable=False)
    appointment_time_end = db.Column(db.Time, nullable=False)
    info = db.Column(db.String, nullable=True)
    rejected = db.Column(db.Boolean, default=False , nullable=False)

    # Relazioni
    availability = db.relationship("Availability", back_populates="appointment")
    account = db.relationship("Account", back_populates="appointment")
    patient = db.relationship("Patient", back_populates="appointment")

    # Metodi
    def to_dict(self):
        return {
            "appointment_id": self.appointment_id,
            "availability_id": self.availability_id,
            "appointment_date": self.appointment_date.isoformat(),
            "appointment_time_start": self.appointment_time_start.strftime("%H:%M"),
            "appointment_time_end": self.appointment_time_end.strftime("%H:%M"),
            "info": self.info,
            "rejected": self.rejected,
            "service_name": self.availability.service.name if self.availability.service else None,
            "service_id": self.availability.service.service_id if self.availability.service else None,
            "location_name": self.availability.location.name if self.availability.location else None,
            "location_address": self.availability.location.address if self.availability.location else None,
            "location_tel_number": self.availability.location.tel_number if self.availability.location else None,
            "patient_name": f"{self.patient.first_name} {self.patient.last_name}" if self.patient else None,
            "operator_name": f"{self.availability.operator.title} {self.availability.operator.first_name} {self.availability.operator.last_name}" if self.availability.operator else None,
            }
    
    # crea un nuovo appuntamento se il paziente non è di default crealo e associarlo all'appuntamento
    def create_new(
            self, 
            patient_first_name,
            patient_last_name,
            patient_email,
            patient_tel_number,
            patient_fiscal_code,
            patient_birth_date,
            patient_is_default ):
 
            if patient_is_default == True:
                patient = Patient.query.filter_by(account_id=self.account_id, is_default=True).first()
                self.patient_id = patient.patient_id

            else:
                # Altrimenti, crea un nuovo paziente
                patient = Patient(
                    account_id=self.account_id,
                    first_name= patient_first_name,
                    last_name=patient_last_name,
                    email=patient_email,
                    tel_number=patient_tel_number,
                    fiscal_code=patient_fiscal_code,
                    birth_date= patient_birth_date,
                    is_default= patient_is_default
                )

                db.session.add(patient)
                # usa il flush per ottenere l'id del paziente
                db.session.flush()
                self.patient_id = patient.patient_id
            db.session.add(self)
            return self
        
    # vincoli

    # evita sovrapposizioni di appuntamenti attivi con lo stesso id di disponibilità, data e ora
    __table_args__ = (
        Index(
            "uq_active_appointments",
            "availability_id",
            "appointment_date",
            "appointment_time_start",
            unique=True,
            postgresql_where=text("rejected = false")
        ),
    )
