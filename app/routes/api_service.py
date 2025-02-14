from app.models.model import Availability, Service, Operator, Location
from flask import jsonify
from app.functions import generate_available_slots
from datetime import datetime, time, timedelta, timezone
from flask import request
from uuid import UUID
from app.routes import bp
from flask import current_app
from flask_jwt_extended import jwt_required


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

def parse_datetime(dt_str: str) -> datetime:
    dt = datetime.fromisoformat(dt_str)
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    return dt

@bp.route('/api/v1/services', methods=['GET'])
@jwt_required()
def get_services():
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '', type=str)
    

    # se è stato fornito un parametro di ricerca filtra i servizi per nome
    services_query = Service.query
    if search:
        services_query = services_query.filter(Service.name.ilike(f"%{search}%"))
    
    services_query = services_query.order_by(Service.name.asc()).paginate(page=page, per_page=per_page, error_out=True)    
    
    return jsonify({
        "page": services_query.page,
        "total": services_query.total,
        "pages": services_query.pages,
        "data": [service.to_dict() for service in services_query.items]
    })

@bp.route('/api/v1/services/<service_id>', methods=['GET'])
@jwt_required()
def get_service(service_id):
    service = Service.query.get(UUID(service_id))
    if service:
        return jsonify(service.to_dict())
    return jsonify({"error": "Service type not found"}), 404

@bp.route('/api/v1/services/<service_id>/available-slots', methods=['GET'])
@jwt_required()
def get_service_availabilities(service_id):

    # imposto i limiti per la data di prenotazione e la data di fine prenotazione 
    # la data di prenotazione non può essere inferiore alla data attuale
    # la data di fine prenotazione non può essere superiore a un anno dalla data attuale

    MIN_RESERVATION_DATETIME = datetime.combine((datetime.now() + timedelta(days=1)).date(), time(0, 0))
    BOOKING_WINDOW_DAYS = 365
    RESERVATION_DATETIME_LIMIT = MIN_RESERVATION_DATETIME + timedelta(days=BOOKING_WINDOW_DAYS)

    try:
        # recupera i parametri dalla query string e li converte in UUID
        service_id = UUID(service_id)
        operator_id = UUID(request.args.get('operator_id')) if request.args.get('operator_id') else None
        location_id = UUID(request.args.get('location_id')) if request.args.get('location_id') else None

        # se è stata fornita una data specifica per restituire gli slot di una data specifica
        page_date_str = request.args.get('page_date') if request.args.get('page_date') else None

        # imposto i cursori per la paginazione se la data arriva con un timezone la converto in UTC
        datetime_from_filter = parse_datetime(request.args.get('datetime_from_filter')) if request.args.get('datetime_from_filter') else MIN_RESERVATION_DATETIME
        datetime_to_filter = parse_datetime(request.args.get('datetime_to_filter')) if request.args.get('datetime_to_filter') else first_day_of_next_month(datetime_from_filter)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify({"error": "Invalid data"}), 400

        # se le date di inizio e fine sono oltre a i limiti imposta al limite

    if datetime_from_filter < MIN_RESERVATION_DATETIME:
        datetime_from_filter = MIN_RESERVATION_DATETIME
    
    if datetime_from_filter > RESERVATION_DATETIME_LIMIT:
        datetime_from_filter = RESERVATION_DATETIME_LIMIT
    

    # se la data di fine è maggiore del limite massimo imposto la data di fine al limite massimo
    if (datetime_to_filter - datetime_from_filter) > (first_day_of_next_month(datetime_from_filter) - datetime_from_filter):
        datetime_to_filter = first_day_of_next_month(datetime_from_filter)

    current_app.logger.info("Datetime filter: %s - %s", datetime_from_filter, datetime_to_filter)
    
    # genera gli slot disponibili

    available_slots = generate_available_slots(datetime_from_filter, datetime_to_filter, service_id, operator_id, location_id)
 
    available_dates_count = len(available_slots.keys())
    available_slots_count = sum(len(available_slots[date]) for date in available_slots.keys())

    current_app.logger.info("Available dates: %d", available_dates_count)
    current_app.logger.info("Available slots: %d", available_slots_count)
    
    # genera i filtri per la selezione degli operatori e dei laboratori    
    # genera la lista di operatori e laboratori disponibili per l'esame selezionato senza duplicati
    # filtrali uno rispetto all'altro se sono stati forniti come parametri 
    distinct_locations_query = Location.query.join(Availability).filter(Availability.service_id == service_id)
    if operator_id:
        distinct_locations_query = distinct_locations_query.filter(Availability.operator_id == operator_id)
    distinct_locations = distinct_locations_query.distinct()

    distinct_operators_query = Operator.query.join(Availability).filter(Availability.service_id == service_id)
    if location_id:
        distinct_operators_query = distinct_operators_query.filter(Availability.location_id == location_id)
    distinct_operators = distinct_operators_query.distinct()
    
    if not available_slots:
        date_list = []
        date_slots = []
    else:
        # se è sono stati genrati slot per il mese corrent oordina le date e popola slots con la prima data disponibile
        # essendo date isoformat posso ordinarlare senza convertirle in datetime
        date_list = sorted(available_slots.keys())
        

    # se è stata fornita una data specifica restituisce gli slot per quella data altrimenti restituisce gli slot per la prima data disponibile
    if not page_date_str and len(date_list) > 0:
        date_slots = available_slots[date_list[0]]
    elif page_date_str in date_list:    
        date_slots = available_slots[page_date_str]
    else:
        date_slots = []

    # calcola i cursori per la paginazione non considera solo il mese e l'anno per poter portare avanti e indietro 
    # il cursore nei mesi di MIN_RESERVATION_DATETIME e RESERVATION_DATETIME_LIMIT
    prev_month = first_day_of_prev_month(datetime_from_filter)
    if (prev_month.year, prev_month.month) < (MIN_RESERVATION_DATETIME.year, MIN_RESERVATION_DATETIME.month):
        prev_cursor_datetime = None
    else:
        prev_cursor_datetime = prev_month.isoformat()

    next_month = first_day_of_next_month(datetime_from_filter)
    if (datetime_from_filter) >= (RESERVATION_DATETIME_LIMIT):
        next_cursor_datetime = None
    else:
        next_cursor_datetime = next_month.isoformat()

    return jsonify({
                "operators": [distinct_operator.to_dict() for distinct_operator in distinct_operators],
                "locations": [distinct_location.to_dict() for distinct_location in distinct_locations],
                "date_list": date_list,
                "slots": date_slots,
                "next_cursor_datetime": next_cursor_datetime,
                "prev_cursor_datetime": prev_cursor_datetime,
            }), 200

