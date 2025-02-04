from pydantic import BaseModel
from uuid import UUID
from datetime import date, time

class Slot(BaseModel):
    availability_id: UUID
    exam_type_name: str
    laboratory_name: str
    laboratory_address: str
    operator_name: str
    availability_date: date
    availability_slot_start: time
    availability_slot_end: time