from app.core.config import settings
import requests
import logging
logger = logging.getLogger("app.services.twilio")
from urllib.parse import urlparse

def initiate_call(to_number: str, from_number: str):
    try:
        if not (settings.twilio_sid and settings.twilio_auth_token and settings.twilio_webhook_base_url):
            return {"sid": "", "error": "twilio_not_configured"}
        parsed = urlparse(settings.twilio_webhook_base_url)
        if not parsed.scheme or parsed.scheme not in ("http", "https"):
            return {"sid": "", "error": "invalid_twilio_webhook_base_url"}
        logger.info(f"Twilio call initiate to={to_number} from={from_number}")
        print(f"[Twilio] initiate_call to={to_number} from={from_number}")
        url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.twilio_sid}/Calls.json"
        twiml_url = f"{settings.twilio_webhook_base_url}/api/calls/twilio-webhook"
        data = {"To": to_number, "From": from_number, "Url": twiml_url, "Method": "POST"}
        resp = requests.post(url, data=data, auth=(settings.twilio_sid, settings.twilio_auth_token), timeout=10)
        resp.raise_for_status()
        payload = resp.json()
        logger.info(f"Twilio call created sid={payload.get('sid')}")
        print(f"[Twilio] call created sid={payload.get('sid')}")
        return payload
    except requests.HTTPError as e:
        body = None
        try:
            body = e.response.text
        except Exception:
            body = None
        logger.error(f"Twilio call error status={getattr(e.response,'status_code',None)} body={body}")
        print(f"[Twilio] call error status={getattr(e.response,'status_code',None)} body={body}")
        return {"sid": "", "error": f"status={getattr(e.response,'status_code',None)} body={body}"}
    except Exception as e:
        logger.error(f"Twilio call error err={e}")
        print(f"[Twilio] call error err={e}")
        return {"sid": "", "error": str(e)}
