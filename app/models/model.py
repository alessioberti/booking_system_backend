import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text, Index
from app.extensions import db
from sqlalchemy_schemadisplay import create_schema_graph
from sqlalchemy import MetaData


class Account(db.Model):
    __tablename__ = "account"

    account_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    email = db.Column(db.String(254), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)
    enabled = db.Column(db.Boolean, default=True, nullable=False)
    failed_login_count = db.Column(db.Integer, default=0)
    last_failed_login = db.Column(db.DateTime, nullable=True)
    last_success_logn = db.Column(db.DateTime, nullable=True)
    is_operator = db.Column(db.Boolean, default=False, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    # Relazioni
    operator = db.relationship("Operator", back_populates="account")
    patient = db.relationship("Patient", back_populates="account")
    appointment = db.relationship("Appointment", back_populates="account")

class Patient(db.Model):
    __tablename__ = "patient"

    patient_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    account_id = db.Column(UUID(as_uuid=True), db.ForeignKey("account.account_id"), nullable=False)
    is_default = db.Column(db.Boolean, default=True, nullable=False)
    first_name = db.Column(db.String(30), nullable=False)
    last_name = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(254), nullable=False)
    tel_number = db.Column(db.String(30), nullable=False)
    fiscal_code = db.Column(db.String(30), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    anonimized = db.Column(db.Boolean, default=False, nullable=False)

    # Relazioni
    account = db.relationship("Account", back_populates="patient")
    appointment = db.relationship("Appointment", back_populates="patient")

class Laboratory(db.Model):
    __tablename__ = "laboratories"

    laboratory_id = db.Column( UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(255), nullable=True)
    tel_number = db.Column(db.String(255), nullable=True)

    # Relazioni
    availability = db.relationship("Availability", back_populates="laboratory")
    laboratory_closure = db.relationship("LaboratoryClosure", back_populates="laboratory")

    # Metodi

    def to_dict(self):
        return {
            "laboratory_id": self.laboratory_id,
            "name": self.name,
        }
    def to_dict_with_info(self):
        return {
            "laboratory_id": self.laboratory_id,
            "name": self.name,
            "address": self.address,
            "tel_number": self.tel_number
        }

class LaboratoryClosure(db.Model):
    __tablename__ = "laboratory_closures"

    closure_id = db.Column( UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    laboratory_id = db.Column( UUID(as_uuid=True), db.ForeignKey("laboratories.laboratory_id"), nullable=False)
    start_datetime = db.Column(db.DateTime, nullable=False)
    end_datetime = db.Column(db.DateTime, nullable=False)

    # Relationships

    laboratory = db.relationship("Laboratory", back_populates="laboratory_closure")

class ExamType(db.Model):
    __tablename__ = "exam_types"

    exam_type_id = db.Column( UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    name = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.String, nullable=True)

     # Relationships
    availability = db.relationship("Availability", back_populates="exam_type")

    # Metodi
    def to_dict(self):
        return {
            "exam_type_id": self.exam_type_id,
            "name": self.name,
            "description": self.description
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
    operator_absences = db.relationship("OperatorAbsence", back_populates="operator")

    # Metodi
    def to_dict(self):
        return {
            "operator_id": self.operator_id,
            "name": f"{self.title} {self.first_name} {self.last_name}",
        }

class OperatorAbsence(db.Model):
    __tablename__ = "operator_absences"

    absence_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    operator_id = db.Column(UUID(as_uuid=True),db.ForeignKey("operators.operator_id"),nullable=False)
    start_datetime = db.Column(db.DateTime, nullable=False)
    end_datetime = db.Column(db.DateTime, nullable=False)

    # Relazioni
    operator = db.relationship("Operator", back_populates="operator_absences")

class Availability(db.Model):
    __tablename__ = "availability"

    availability_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False )
    exam_type_id = db.Column(UUID(as_uuid=True),db.ForeignKey("exam_types.exam_type_id"),nullable=False)
    laboratory_id = db.Column(UUID(as_uuid=True),db.ForeignKey("laboratories.laboratory_id"),nullable=False)
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

    laboratory = db.relationship("Laboratory", back_populates="availability")
    operator = db.relationship("Operator", back_populates="availability")
    exam_type = db.relationship("ExamType", back_populates="availability")
    appointment = db.relationship("Appointment", back_populates="availability")

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

    # unique constraint per evitare sovrapposizioni di appuntamenti attivi con lo stesso id di disponibilità, data e ora

    __table_args__ = (
        Index(
            "uq_active_appointments",
            "availability_id",
            "appointment_date",
            "appointment_time_start",
            unique=True,
            postgresql_where=text("NOT rejected")
        ),
    )

    # Metodi per la rappresentazione a stringa

    def to_dict(self):
        return {
            "appointment_id": self.appointment_id,
            "account_id": self.account_id,
            "patient_id": self.patient_id,
            "availability_id": self.availability_id,
            "appointment_date": self.appointment_date,
            "appointment_time_start": self.appointment_time_start,
            "appointment_time_end": self.appointment_time_end,
            "info": self.info,
            "rejected": self.rejected
        }