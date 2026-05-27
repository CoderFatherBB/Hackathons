from app.tasks.celery_app import celery_app
from app.services.whisper import transcribe
from app.services.groq import classify_sales

@celery_app.task
def score_recording(audio_bytes: bytes):
    transcript = transcribe(audio_bytes)
    return classify_sales(transcript)
