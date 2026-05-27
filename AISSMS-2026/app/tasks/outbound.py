from app.tasks.celery_app import celery_app
from app.services.twilio import initiate_call
import logging
logger = logging.getLogger("app.tasks.outbound")

@celery_app.task
def call_lead(to_number: str, from_number: str):
    logger.info(f"call_lead started to={to_number} from={from_number}")
    print(f"[Celery] call_lead start to={to_number} from={from_number}")
    result = initiate_call(to_number, from_number)
    logger.info(f"call_lead result={result}")
    print(f"[Celery] call_lead result={result}")
    return result
