from app.core.config import settings
import requests
from uuid import uuid4
from app.services.memory import client as redis_client

def synthesize(text: str):
    if not settings.elevenlabs_api_key:
        return None
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{settings.elevenlabs_voice_id}"
    headers = {
        "xi-api-key": settings.elevenlabs_api_key,
        "accept": "audio/mpeg",
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "model_id": settings.elevenlabs_model_id,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }
    resp = requests.post(url, json=payload, headers=headers, timeout=15)
    resp.raise_for_status()
    audio = resp.content
    key = uuid4().hex
    try:
        redis_client.set(f"audio:{key}", audio, ex=3600)
        return f"{settings.twilio_webhook_base_url}/api/calls/audio/{key}.mp3"
    except Exception:
        return None
