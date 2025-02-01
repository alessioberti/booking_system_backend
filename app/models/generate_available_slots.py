from datetime import date, datetime, timedelta
from flask import current_app

# funzione per gestire l'aggiunta di minuti ad un oggetto time. non è necessario gestire il giorno successivo
def add_minutes_to_time(original_time, minutes_to_add):
    temp_datetime = datetime.combine(date.today(), original_time)
    temp_datetime += timedelta(minutes=minutes_to_add)
    return temp_datetime.time()

#funzione per verificare se uno slot è già stato prenotato
def slot_is_booked(availability_id, availability_date, availability_slot_start, availability_slot_end, appointments):
    
    return any(
        str(availability_id) == str(booked_slot.availability_id) and
        availability_date == booked_slot.appointment_date and
        availability_slot_start == booked_slot.appointment_time_start and
        availability_slot_end == booked_slot.appointment_time_end
        for booked_slot in appointments
    )

#funzione per verificare se uno slot è in un periodo di chiusura di un laboratorio 
def lab_is_closed(laboratory_id, availability_date, availability_slot_start, availability_slot_end, laboratory_closures):
    slot_start_datetime = datetime.combine(availability_date, availability_slot_start)
    slot_end_datetime = datetime.combine(availability_date, availability_slot_end)

    return any(
        str(laboratory_id) == str(laboratory_closure.laboratory_id) and
        slot_start_datetime < laboratory_closure.end_datetime and
        slot_end_datetime > laboratory_closure.start_datetime
        for laboratory_closure in laboratory_closures
    )

#funzione per verificare se uno slot è in un periodo di assenza di un operatore 
def operator_is_absent(operator_id, availability_date ,availability_slot_start, availability_slot_end, operator_absences):
    slot_start_datetime = datetime.combine(availability_date, availability_slot_start)
    slot_end_datetime = datetime.combine(availability_date, availability_slot_end)

    return any(
        str(operator_id) == str(operator_absence.operator_id) and
        slot_start_datetime < operator_absence.end_datetime and
        slot_end_datetime > operator_absence.start_datetime
        for operator_absence in operator_absences
    )

#funzione per generare slot prenotabili a partire dalle disponibilità degli operatori datetime_from_filter viene utilizzato come parametro nella route per non fornire date nel passato
def generate_available_slots(availabilities, datetime_from_filter = None, datetime_to_filter = None, laboratory_closures = None, operator_absences = None, appointments = None):
    
    if not availabilities:
        current_app.logger.debug("No operators availability provided.")
        return []
    
    availabilities_slots_dategroup = {}
    
    for availability in availabilities:
        
        current_app.logger.debug(
            "Processing availability_id=%s, dal %s al %s, weekday=%d",
            availability.availability_id,
            availability.available_from_date,
            availability.available_to_date,
            availability.available_weekday
        )
        
     
        # se datetime_from_filter è impostato filtra la disponibilià degli esami partendo da quella data (se maggiore)
        if  isinstance(datetime_from_filter, datetime):
            availability_date = max(availability.available_from_date, datetime_from_filter.date())
        else:
            availability_date = availability.available_from_date

        # se datetime_to_filter è impostato filtra la disponibilità degli esami fino a quella data (se inferiore)
        if  isinstance(datetime_to_filter, datetime):
            availability_maxdate = min(datetime_to_filter.date(), availability.available_to_date)
        else:
            availability_maxdate = availability.available_to_date

        current_app.logger.debug(
            "Filtered date range: %s - %s",
            availability_date,
            availability_maxdate
        )

        # sposta availability date al primo giorno della settimana indicato nella availability
        availability_date += timedelta(days=((availability.available_weekday - availability_date.weekday()) % 7))
        # per ciascun giorno fino a fine disponibilià compresa 
        while availability_date <= availability_maxdate:
            # imposta la partenza del primo slot sempre all'orario di partenza delle disponibiltà (necessario per generare gli slot in modo univoco)
            availability_slot_start = availability.available_from_time
            
            # per ciascun giorno crea gli slot in fino all'ora di di fine disponibilità
            while availability_slot_start < availability.available_to_time:
                # calcola la fine dello slot
                availability_slot_end = add_minutes_to_time(availability_slot_start, availability.slot_duration_minutes)
                # se lo slot supera l'orario esci e passa alla settimana successiva
                if availability_slot_end > availability.available_to_time:
                   break

                slot = {
                    "availability_id": availability.availability_id,
                   # "exam_type_id": str(availability.exam_type_id),
                   # "laboratory_id": str(availability.laboratory_id),
                   # "operator_id": str(availability.operator_id),
                    "exam_type_name": availability.exam_type.name,
                    "laboratory_name": availability.laboratory.name,
                    "laboratory_address": availability.laboratory.address,
                    "operator_name": "availability.operator.title availability.operator.first_name availability.operator.last_name",
                    "availability_date":  availability_date.isoformat(),
                    "availability_slot_start": availability_slot_start.isoformat(timespec='minutes'),
                    "availability_slot_end": availability_slot_end.isoformat(timespec='minutes')
                }

                # se lo slot è dopo l'orario del filtro e se è il laboratorio non è chiuso l'oepratore in ferie e lo slot non è già prenotato
                if (
                    # filtra gli slot in base all'orario di inizio e fine impostato nei parametri
                    ((datetime_from_filter == None) or (datetime.combine(availability_date, availability_slot_start) >= datetime_from_filter)) and
                    (datetime_to_filter is None or datetime.combine(availability_date, availability_slot_end) <= datetime_to_filter) and
                    # filtra gli slot in base alle chiusure del laboratorio
                    ((laboratory_closures == None) or (not lab_is_closed(availability.laboratory_id, availability_date, availability_slot_start, availability_slot_end, laboratory_closures))) and 
                    # filtra gli slot in base alle assenze dell'operatore
                    ((operator_absences == None) or (not operator_is_absent(availability.operator_id, availability_date ,availability_slot_start, availability_slot_end, operator_absences))) and 
                    # filtra gli slot in base alle prenotazioni già effettuate
                    ((appointments == None) or (not slot_is_booked(availability.availability_id, availability_date, availability_slot_start, availability_slot_end, appointments)))):

                    # aggiungi lo slot all'array
                    #availabilities_slots.append(slot)
                    if availability_date.isoformat() in availabilities_slots_dategroup:
                        availabilities_slots_dategroup[availability_date.isoformat()].append(slot)
                    else:
                        availabilities_slots_dategroup[availability_date.isoformat()] = [slot]

                #passa allo slot successivo
                availability_slot_start = add_minutes_to_time(availability_slot_end, availability.pause_minutes)
            # passa alla settimana successiva
            availability_date += timedelta(days=7)

    current_app.logger.debug("Generated for %d dates", len(availabilities_slots_dategroup))
    current_app.logger.debug("Generated %d slots", sum(len(slots) for slots in availabilities_slots_dategroup.values()))

    return availabilities_slots_dategroup