from datetime import date, datetime, timedelta
from flask import current_app
from app.models.model import Availability, Appointment, LocationClosure, OperatorAbsence


# aggiunge minuti ad un orario (non considera il cambio di giorno)
def add_minutes_to_time(original_time, minutes_to_add):
        temp_datetime = datetime.combine(date.today(), original_time)
        temp_datetime += timedelta(minutes=minutes_to_add)
        return temp_datetime.time()

# recupera le disponibilità attive con filtri per data, tipo esame, operatore e laboratorio (se speficiati) e in sovrapposizione con date e orari (se specificati)
def get_enabled_availabilities(from_datetime = None, to_datetime = None, service_id = None, operator_id = None, location_id = None):
    query = Availability.query.filter(Availability.enabled == True)
    if service_id:
        query = query.filter(Availability.service_id == service_id)
    if operator_id:
        query = query.filter(Availability.operator_id == operator_id)
    if location_id:
        query = query.filter(Availability.location_id == location_id)
    # esclude le disponibilità che finiscono prima di from_datetime e quelle che iniziano dopo to_datetime
    if from_datetime:
        query = query.filter(Availability.available_to_date >= from_datetime.date())
    if to_datetime:
        query = query.filter(Availability.available_from_date <= to_datetime.date())
    return query.all()
    
# recupera le chiusure per laborariorio (se specificato) e in sovrapposizione con date e orari (se specificati)
def get_location_closures(from_datetime = None, to_datetime = None, location_id = None):
    query = LocationClosure.query
    if location_id:
        query = query.filter(LocationClosure.location_id == location_id)
    if from_datetime:
        query = query.filter(LocationClosure.end_datetime > from_datetime)
    if to_datetime:
        query = query.filter(LocationClosure.start_datetime < to_datetime)
    
    
    return query.all()
    
# recupera le assenze per operatore (se specificato) e in sovrapposizione con date e orari (se specificati)
def get_operator_absences(from_datetime = None, to_datetime = None, operator_id = None):
    query = OperatorAbsence.query
    if operator_id:
        query = query.filter(OperatorAbsence.operator_id == operator_id)
    if from_datetime:
        query = query.filter(OperatorAbsence.end_datetime > from_datetime)
    if to_datetime:
        query = query.filter(OperatorAbsence.start_datetime < to_datetime)
    
    return query.all()
        
#recupera slot già prenotati (non rejected) la cui data di appuntamento è in sovrapposizione al filtro
def get_active_appointments(from_datetime=None, to_datetime=None):
    
    query = Appointment.query.filter(Appointment.rejected == False)
    if from_datetime:
        query = query.filter(Appointment.appointment_date >= from_datetime.date())
    if to_datetime:
        query = query.filter(Appointment.appointment_date <= to_datetime.date())
        
    return query.all()

# verifica se il laboratorio è chiuso per un laborio specifico
def is_location_id_closed(location_closures, location_id, slot_start_datetime, slot_end_datetime):
    if not location_closures:
        return False
    else: 
        return any(
            location_id == location_closure.location_id and
                slot_start_datetime < location_closure.end_datetime and
                slot_end_datetime > location_closure.start_datetime
            for location_closure in location_closures
        ) 

# verifica se l'operatore è assente in un intervallo di date e orario
def is_operator_id_absent(operator_absences , operator_id, slot_start_datetime, slot_end_datetime):
    if not operator_absences:
        return False
    else:
        return any(
            operator_id == operator_absence.operator_id and
            slot_start_datetime < operator_absence.end_datetime and
            slot_end_datetime > operator_absence.start_datetime
            for operator_absence in operator_absences
        ) 

# verifica se esiste lo slot è già stato prenotato in relazione ad una regola di disponibilità
def is_slot_booked(appointments, availability_id, appointment_date, from_time, to_time):
    
    if not appointments:
        return False
    else:
        return any(
            availability_id == booked_slot.availability_id and
            appointment_date == booked_slot.appointment_date and
            from_time == booked_slot.appointment_time_start and
            to_time == booked_slot.appointment_time_end
            for booked_slot in appointments
        )
    
def generate_available_slots(
    datetime_from_filter = None, 
    datetime_to_filter = None, 
    service_id = None,
    operator_id = None,
    location_id = None,
    exclude_location_closure_slots = True, 
    exclude_operator_absence_slots = True, 
    exclude_booked_slots= True
    ):
    
    availabilities_slots_dategroup = {}
    
    # Recupera le disponibilità attive con i filtri se applicati
    availabilities = get_enabled_availabilities(datetime_from_filter, datetime_to_filter, service_id, operator_id, location_id)
    
    # se le esclusioni sono attivate recupera le chiusure, le assenze e gli appuntamenti attivi con i filtri se applicati
    if exclude_location_closure_slots:
        location_closures = get_location_closures(datetime_from_filter, datetime_to_filter, location_id)
    if exclude_operator_absence_slots:
        operator_absences = get_operator_absences(datetime_from_filter, datetime_to_filter, operator_id)
    if exclude_booked_slots:
        appointments = get_active_appointments(datetime_from_filter, datetime_to_filter)
    
    # se non ci sono disponibilità esci
    if not availabilities:
        current_app.logger.info("No operators availability provided.")
        return availabilities_slots_dategroup
    
    for availability in availabilities:
        current_app.logger.debug("Processing availability_id=%s", availability.availability_id)
        
        # Sovrascrivi le date della disponibilità basandoti sui filtri se impostati e se sono più restrittivi rispetto alla regola di disponibilità
        
        if  isinstance(datetime_from_filter, datetime):
            appointment_date = max(availability.available_from_date, datetime_from_filter.date())
        else:
            appointment_date = availability.available_from_date
        if  isinstance(datetime_to_filter, datetime):
            availability_maxdate = min(datetime_to_filter.date(), availability.available_to_date)
        else:
            availability_maxdate = availability.available_to_date
            
        #current_app.logger.debug("Filtered date range: %s - %s",appointment_date,availability_maxdate)
        
        # sposta availability date al primo giorno della settimana indicato nella availability
        appointment_date += timedelta(days=((availability.available_weekday - appointment_date.weekday()) % 7))
        
        # per ciascun giorno fino a fine disponibilià compresa
        while appointment_date <= availability_maxdate:
            
            # imposta la partenza del primo slot sempre all'orario di partenza delle disponibiltà (necessario per generare gli slot in modo univoco)
            appointment_time_start = availability.available_from_time
            # per ciascun giorno crea gli slot in fino all'ora di di fine disponibilità
            while appointment_time_start < availability.available_to_time:
                
                # calcola la fine dello slot
                appointment_time_end = add_minutes_to_time(appointment_time_start, availability.slot_duration_minutes)
                
                # se lo slot supera l'orario esci dal ciclo e passa alla settimana successiva
                if appointment_time_end > availability.available_to_time:
                   break
                
                slot = {
                    "availability_id": availability.availability_id,
                    "service_name": availability.service.name,
                    "location_name": availability.location.name,
                    "location_address": availability.location.address,
                    "location_tel_number": availability.location.tel_number,
                    "operator_name": f"{availability.operator.title} {availability.operator.first_name} {availability.operator.last_name}",
                    "appointment_date":  appointment_date.isoformat(),
                    "appointment_time_start": appointment_time_start.isoformat(timespec='minutes'),
                    "appointment_time_end": appointment_time_end.isoformat(timespec='minutes')
                }
                
                slot_start_datetime = datetime.combine(appointment_date, appointment_time_start)
                slot_end_datetime = datetime.combine(appointment_date, appointment_time_end)
                
                # se attivati i filtri escludi gli slot che non soddisfano le condizioni
                exclude_conditions = []
                # escludi lo slot se precede l'orario (time) di inizio filtro
                if datetime_from_filter:
                    exclude_conditions.append(slot_start_datetime < datetime_from_filter)
                # escludi lo slot se supera l'orario (time) di fine filtro
                if datetime_to_filter:
                    exclude_conditions.append(slot_end_datetime > datetime_to_filter)
                # esecludi lo slot se è già prenotato
                if exclude_booked_slots:
                    exclude_conditions.append(is_slot_booked(appointments, availability.availability_id, appointment_date, appointment_time_start, appointment_time_end))
                # escludi lo slot se l'operatore è assente
                if exclude_operator_absence_slots:
                    exclude_conditions.append(is_operator_id_absent(operator_absences, availability.operator_id, slot_start_datetime, slot_end_datetime))
                # escludi lo slot se il laboratorio è chiuso
                if exclude_location_closure_slots:
                    exclude_conditions.append(is_location_id_closed(location_closures, availability.location_id, slot_start_datetime, slot_end_datetime))
                
                # se uno dei filtri indicati è vero scarta lo slot
                if any(exclude_conditions):
                    appointment_time_start = add_minutes_to_time(appointment_time_end, availability.pause_minutes)
                    continue
                    
                # se lo slot è valido aggiungilo al dizionario
            
                if appointment_date.isoformat() in availabilities_slots_dategroup:
                    availabilities_slots_dategroup[appointment_date.isoformat()].append(slot)
                else:
                    availabilities_slots_dategroup[appointment_date.isoformat()] = [slot]
                appointment_time_start = add_minutes_to_time(appointment_time_end, availability.pause_minutes)
            # passa alla settimana successiva
            appointment_date += timedelta(days=7)
    
    current_app.logger.debug("Generated for %d dates", len(availabilities_slots_dategroup))
    current_app.logger.debug("Generated %d slots", sum(len(slots) for slots in availabilities_slots_dategroup.values()))
            
    return availabilities_slots_dategroup