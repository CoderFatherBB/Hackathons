from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "voice_agent",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.outbound"],
)
print("[Celery] Initialized app with broker/backend:", settings.redis_url)
