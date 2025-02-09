from app.models.model import Availability, ExamType, Operator, Laboratory
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

@bp.route('/api/v1/exams', methods=['GET'])
@jwt_required()
def get_exam_types():
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    exam_types_query= ExamType.query.join(Availability).filter(Availability.enabled == True).paginate(page=page, per_page=per_page, error_out=True)

    return jsonify({
        "page": exam_types_query.page,
        "total": exam_types_query.total,
        "pages": exam_types_query.pages,
        "data": [exam_type.to_dict() for exam_type in exam_types_query.items]
    })

@bp.route('/api/v1/exams/<exam_type_id>', methods=['GET'])
@jwt_required()
def get_exam_type(exam_type_id):
    exam_type = ExamType.query.get(UUID(exam_type_id))
    if exam_type:
        return jsonify(exam_type.to_dict())
    return jsonify({"error": "Exam type not found"}), 404

@bp.route('/api/v1/exams/<exam_type_id>/available-slots', methods=['GET'])
@jwt_required()
def get_exam_type_availabilities(exam_type_id):

    # imposto i limiti per la data di prenotazione e la data di fine prenotazione 
    # la data di prenotazione non può essere inferiore alla data attuale
    # la data di fine prenotazione non può essere superiore a un anno dalla data attuale

    MIN_RESERVATION_DATETIME = datetime.combine((datetime.now() + timedelta(days=1)).date(), time(0, 0))
    BOOKING_WINDOW_DAYS = 365
    RESERVATION_DATETIME_LIMIT = MIN_RESERVATION_DATETIME + timedelta(days=BOOKING_WINDOW_DAYS)

    try:
        # recupera i parametri dalla query string e li converte in UUID
        exam_type_id = UUID(exam_type_id)
        operator_id = UUID(request.args.get('operator_id')) if request.args.get('operator_id') else None
        laboratory_id = UUID(request.args.get('laboratory_id')) if request.args.get('laboratory_id') else None

        # se è stata fornita una data specifica per restituire gli slot di una data specifica
        page_date_str = request.args.get('page_date')
        if page_date_str:
            try:
                page_date = datetime.strptime(page_date_str, "%Y-%m-%d")
            except:
                return  jsonify({"error": "Invalid date format"}), 400
        else:
            page_date = None

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

    available_slots = generate_available_slots(datetime_from_filter, datetime_to_filter, exam_type_id, operator_id, laboratory_id)
 
    available_dates_count = len(available_slots.keys())
    available_slots_count = sum(len(available_slots[date]) for date in available_slots.keys())

    current_app.logger.info("Available dates: %d", available_dates_count)
    current_app.logger.info("Available slots: %d", available_slots_count)
    
    # genera i filtri per la selezione degli operatori e dei laboratori    
    # genera la lista di operatori e laboratori disponibili per l'esame selezionato senza duplicati
    # filtrali uno rispetto all'altro se sono stati forniti come parametri 
    distinct_laboratories_query = Laboratory.query.join(Availability).filter(Availability.exam_type_id == exam_type_id)
    if operator_id:
        distinct_laboratories_query = distinct_laboratories_query.filter(Availability.operator_id == operator_id)
    distinct_laboratories = distinct_laboratories_query.distinct()

    distinct_operators_query = Operator.query.join(Availability).filter(Availability.exam_type_id == exam_type_id)
    if laboratory_id:
        distinct_operators_query = distinct_operators_query.filter(Availability.laboratory_id == laboratory_id)
    distinct_operators = distinct_operators_query.distinct()
    
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
                "laboratories": [distinct_laboratory.to_dict() for distinct_laboratory in distinct_laboratories],
                "date_list": date_list,
                "slots": date_slots,
                "next_cursor_datetime": next_cursor_datetime,
                "prev_cursor_datetime": prev_cursor_datetime,
            }), 200

