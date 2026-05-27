import os
from dotenv import load_dotenv

class Settings:
    def __init__(self):
        load_dotenv()
        self.app_name = os.getenv("APP_NAME", "AI Voice Agent Platform")
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.groq_model_name = os.getenv("GROQ_MODEL_NAME", "llama3-8b-8192")
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        self.elevenlabs_voice_id = os.getenv("ELEVENLABS_VOICE_ID", "Bella")
        self.elevenlabs_model_id = os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")
        self.twilio_sid = os.getenv("TWILIO_SID")
        self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_from_number = os.getenv("TWILIO_FROM_NUMBER")
        self.twilio_webhook_base_url = os.getenv("TWILIO_WEBHOOK_BASE_URL")
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./local.db")
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.s3_bucket = os.getenv("S3_BUCKET")
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_region = os.getenv("AWS_REGION")
        self.whisper_endpoint = os.getenv("WHISPER_ENDPOINT")
        self.max_llm_tokens = int(os.getenv("MAX_LLM_TOKENS", "256"))
        self.voice_greeting_message = os.getenv("VOICE_GREETING_MESSAGE", "Hello from AI Voice Agent. We help automate outreach and support. Please speak after the beep.")

settings = Settings()
