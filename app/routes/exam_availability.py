from flask import Blueprint
from app.models.model import Appointment, Availability, ExamType, OperatorAbsence, LaboratoryClosure, Operator, Laboratory
from flask import jsonify
from app.models.generate_available_slots import generate_available_slots
from datetime import datetime, time, timedelta
from flask import request
from uuid import UUID
from sqlalchemy.orm import joinedload
from app.routes import bp
from flask import current_app

# funzioni per ottenere il primo giorno del mese successivo e del mese precedente
# le date sono impostate a mezzanotte per forzare un limite inclusivo per la data di inizio e esclusivo per la data di fine
def first_day_of_next_month(dt: datetime) -> datetime:
    if dt.month == 12:
        return datetime(dt.year + 1, 1, 1 ,0, 0)
    return datetime(dt.year, dt.month + 1, 1, 0, 0)
def first_day_of_prev_month(dt: datetime) -> datetime:
    if dt.month == 1:
        return datetime(dt.year - 1, 12, 1 ,0, 0)
    return datetime(dt.year, dt.month - 1, 1, 0, 0)

@bp.route('/api/v1/exam_type', methods=['GET'])
def get_exam_types():
    exam_types = ExamType.query.join(Availability).options(joinedload(ExamType.availability)).filter(Availability.enabled == True).all()
    return jsonify([exam_type.to_dict() for exam_type in exam_types])

@bp.route('/api/v1/exam_type/<exam_type_id>/availability', methods=['GET'])
def get_exam_type_availabilities(exam_type_id):

    # imposto i limiti per la data di prenotazione e la data di fine prenotazione 
    # la data di prenotazione non può essere inferiore alla data attuale
    # la data di fine prenotazione non può essere superiore a un anno dalla data attuale

    MIN_RESERVATION_DATETIME = datetime.combine((datetime.now() + timedelta(days=1)).date(), time(0, 0))
    RESERVATION_DATETIME_LIMIT = datetime.combine((datetime.now() + timedelta(days=365)).date(), time(0, 0))

    # recupera i parametri dalla query string e li converte in UUID
    exam_type_id = UUID(exam_type_id)
    operator_id = UUID(request.args.get('operator_id')) if request.args.get('operator_id') else None
    laboratory_id = UUID(request.args.get('laboratory_id')) if request.args.get('laboratory_id') else None

    # se è stata fornita una data specifica per restituire gli slot di una data specifica
    page_date_str = request.args.get('page_date')
    if page_date_str:
        try:
            page_date = datetime.fromisoformat(page_date_str)
        except:
            return  jsonify({"error": "Invalid date format"}), 400
    else:
        page_date = None

    # imposto i cursori per la paginazione
    datetime_from_filter = datetime.fromisoformat(request.args.get('datetime_from_filter')) if request.args.get('datetime_from_filter') else MIN_RESERVATION_DATETIME
    datetime_to_filter = datetime.fromisoformat(request.args.get('datetime_to_filter')) if request.args.get('datetime_to_filter') else first_day_of_next_month(datetime_from_filter)
    #initial_datetime_from_filter = datetime.fromisoformat(request.args.get('initial_cursor_datetime')) if request.args.get('initial_cursor_datetime') else datetime_from_filter

    if datetime_from_filter < MIN_RESERVATION_DATETIME:
        datetime_from_filter = MIN_RESERVATION_DATETIME
    
    if datetime_from_filter >= RESERVATION_DATETIME_LIMIT or datetime_to_filter >= RESERVATION_DATETIME_LIMIT:

        current_app.logger.info("Datetime filter is greater than reservation limit")
        return jsonify([]), 200

    # se la data di fine è maggiore del limite massimo imposto la data di fine al limite massimo
    if (datetime_to_filter - datetime_from_filter) > (first_day_of_next_month(datetime_from_filter) - datetime_from_filter):
        datetime_to_filter = first_day_of_next_month(datetime_from_filter)

    # recuperata le disponibilità per l'esame selezionato filtrando quelle nel passato e quelle oltre la data di fine prenotazione
    # l'intervallo è chiuso perchè se coincide con la data di inizio o fine prenotazione deve essere considerato
    availabilities_query = (
        Availability.query
        .filter(Availability.exam_type_id == exam_type_id)
        .filter(Availability.enabled == True)
        .filter(Availability.available_from_date <= datetime_to_filter.date(), Availability.available_to_date >= datetime_from_filter.date())
    )

    if operator_id:
        availabilities_query = availabilities_query.filter(Availability.operator_id == operator_id)
    if laboratory_id:
        availabilities_query = availabilities_query.filter(Availability.laboratory_id == laboratory_id)
    
    availabilities = availabilities_query.all()

    # se non ci sono disponibilità restituisce un array vuoto
    if not availabilities:

        current_app.logger.info("No availabilities found for exam_type_id=%s", exam_type_id)

        return jsonify([]), 200

    # recupera le chiusure dei laboratori se è stato fornito un laboratorio specifico oppure recupera tutte le chiusure dei laboratori per l'esame selezionato
    laboratory_closures_query = (
        LaboratoryClosure.query
        .filter(LaboratoryClosure.start_datetime < datetime_to_filter, LaboratoryClosure.end_datetime > datetime_from_filter)
    )

    # se è impostato un laboratorio specifico filtra le chiusure per quel laboratorio
    if laboratory_id:
        laboratory_closures_query = laboratory_closures_query.filter(LaboratoryClosure.laboratory_id == laboratory_id)

    # filtra le chiusure per l'esame selezionato e rimuove i duplicati

    laboratory_closures_query = (laboratory_closures_query 
            .join(Laboratory) 
            .join(Availability) 
            .filter(Availability.exam_type_id == exam_type_id)
            .distinct()
    )
       
    laboratory_closures = laboratory_closures_query.all()

    # recupera le assenze degli operatori se è stato fornito un operatore specifico oppure recupera tutte le assenze degli operatori per l'esame selezionato
    operator_absences_query = (
        OperatorAbsence.query
        .filter(OperatorAbsence.start_datetime < datetime_to_filter, OperatorAbsence.end_datetime > datetime_from_filter)
    )

    # se è impostato un operatore specifico filtra le assenze per quell'operatore
    if operator_id:
        operator_absences_query = operator_absences_query.filter(OperatorAbsence.operator_id == operator_id)
    
    # filtra le assenze per l'esame selezionato e rimuove i duplicati
    operator_absences_query = (operator_absences_query
            .join(Operator)
            .join(Availability)
            .filter(Availability.exam_type_id == exam_type_id)
            .distinct()
        )

    operator_absences = operator_absences_query.all()

    # recupera gli appuntamenti già prenotati per l'esame selezionato
    appointments_query = (
        Appointment.query
        .join(Availability)
        .filter(Appointment.rejected == False)
        .filter(Appointment.appointment_date >= datetime_from_filter.date())
        .filter(Appointment.appointment_date <= datetime_to_filter.date())
        .filter(Availability.exam_type_id == exam_type_id)
    )

    # filtri per operatori e laboratori
    if operator_id:
        appointments_query = appointments_query.filter(Availability.operator_id == operator_id)
    
    if laboratory_id:
        appointments_query = appointments_query.filter(Availability.laboratory_id == laboratory_id)
    
    appointments = appointments_query.all()

    # genera gli slot disponibili

    available_slots = generate_available_slots(availabilities, datetime_from_filter, datetime_to_filter, laboratory_closures, operator_absences, appointments)

    available_dates_count = len(available_slots.keys())
    available_slots_count = sum(len(available_slots[date]) for date in available_slots.keys())

    current_app.logger.debug("Available dates: %d", available_dates_count)
    current_app.logger.debug("Available slots: %d", available_slots_count)
    
    # genera i filtri per la selezione degli operatori e dei laboratori    
    # genera la lista di operatori e laboratori disponibili per l'esame selezionato senza duplicati
    laboratory_list = [laboratory.to_dict() for laboratory in Laboratory.query.join(Availability).filter(Availability.exam_type_id == exam_type_id).distinct().all()]
    operator_list = [operator.to_dict() for operator in Operator.query.join(Availability).filter(Availability.exam_type_id == exam_type_id).distinct().all()]

    if not available_slots:
        date_list = []
        date_slots = []
    else:
        # se è sono stati genrati slot per il mese corrent oordina le date e popola slots con la prima data disponibile
        # essendo date isoformat posso ordinarlare senza convertirle in datetime
        date_list = sorted(available_slots.keys())
        date_slots = available_slots[date_list[0]]

    # se è stata fornita una data specifica restituisce gli slot per quella data
    if page_date and page_date.isoformat() in date_list:
        date_slots = available_slots[page_date.isoformat()]

    # calcola i cursori per la paginazione
    prev_month = first_day_of_prev_month(datetime_from_filter)
    if prev_month < MIN_RESERVATION_DATETIME:
        prev_cursor_datetime = None
    else:
        prev_cursor_datetime = prev_month.isoformat()
    
    next_month = first_day_of_next_month(datetime_from_filter)
    if next_month >= RESERVATION_DATETIME_LIMIT:
        next_cursor_datetime = None
    else:
        next_cursor_datetime = next_month.isoformat()

    return jsonify({
                "operators": operator_list,
                "laboratories": laboratory_list,
                "date_list": date_list,
                "slots": date_slots,
                "next_cursor_datetime": next_cursor_datetime,
                "prev_cursor_datetime": prev_cursor_datetime,
                #"initial_datetime_from_filter": initial_datetime_from_filter.isoformat()
            }), 200
