<div align="center">
  <h1 align="center">Aissms-2026</h1>
  <p align="center">
    <strong>Project from the <a href="https://github.com/CoderFatherBB/Hackathons">Hackathons</a> Repository</strong>
  </p>
</div>

---

## 📖 Overview

Welcome to the **Aissms-2026** project! This directory contains the specific source code, resources, and implementation details for this project.

### Existing Documentation\n\n# AI Voice Agent & Call Intelligence Platform

## Overview
Production-ready backend for:
- Outbound AI Voice Agent
- Inbound AI Customer Support Agent
- Call Upload + Agent Performance Scoring Dashboard

## Tech Stack
- FastAPI (Python 3.11), SQLAlchemy, Pydantic
- LLM: Groq Cloud API
- TTS: ElevenLabs
- STT: Whisper
- Telephony: Twilio
- DB: PostgreSQL (default SQLite for dev)
- Cache/Jobs: Redis + Celery
- Deployment: Docker + docker-compose
- Object Storage: S3

## Current Implementation
- Modular routers under `app/routers` for leads, calls, analysis, dashboard.
- Database models under `app/models/models.py` for users, leads, calls, call_messages, agent_scores, escalations.
- Central config at `app/core/config.py` reading `.env` with safe defaults.
- DB session setup `app/core/db.py`; schema auto-created on startup.
- Service stubs in `app/services` for Groq, ElevenLabs, Whisper, Twilio, S3, and Redis memory.
- Celery app and tasks in `app/tasks` for outbound calling and scoring hooks.
- Role guard for dashboard using `X-Role` header.
- Entrypoint `main.py` mounting all routers.

## Environment Variables
Place in `.env`:
```
GROQ_API_KEY=...
GROQ_MODEL_NAME=llama3-70b-8192
ELEVENLABS_API_KEY=...
TWILIO_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_FROM_NUMBER=+1...
DATABASE_URL=postgresql+psycopg2://app:app@postgres:5432/appdb
REDIS_URL=redis://redis:6379/0
S3_BUCKET=...
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=...
WHISPER_ENDPOINT=http://whisper_service:9000/
```
(Dev defaults exist; unset keys run in stub mode.)

## API Routes
- `/api/leads`
  - POST `/create`
  - GET `/{lead_id}`
  - PUT `/update-status`
- `/api/calls`
  - POST `/initiate-outbound-call`
  - POST `/twilio-webhook`
  - POST `/recording-webhook`
  - GET `/{call_id}`
- `/api/analysis`
  - POST `/upload-call`
  - POST `/score-call`
  - GET `/agent/{agent_id}/report`
- `/api/dashboard` (requires `X-Role: admin|supervisor`)
  - GET `/metrics`
  - GET `/leaderboard`

## Running
### Local
```
pip install -r requirements.txt  # or use Docker
python -m uvicorn main:app --reload
```

### Docker
```
docker-compose up --build
```

## Testing
Pytest is configured to run unit tests. If imports fail, run:
```
PYTHONPATH=. pytest -q
```
Current test covers `utils.llm.get_llm_response` via a shim at `utils/llm.py` pointing to `app.utils.llm`.

## Next Steps
- Wire real Groq prompts and ElevenLabs streaming to Twilio.
- Implement Whisper transcription and attach transcripts to calls.
- Build intent router for inbound and integrate internal APIs.
- Add JWT auth and RBAC to dashboard.
- Add audit logging and guardrails for LLM I/O.\n

---

## 🚀 Getting Started

### Prerequisites
Make sure you have the necessary environment setup to run or build this project. Depending on the repository's technology stack, you may need:
- Standard language compilers/interpreters (e.g., Python, C++, Java).
- Required frameworks and libraries as per the codebase.

### Running the Code
1. Ensure you are in the project directory:
   ```bash
   cd "AISSMS-2026"
   ```
2. Execute the main scripts or compile the source code according to the language standards.

---

## 👤 Author

**Bhavin Baldota**

- LinkedIn: [Bhavin Baldota](https://www.linkedin.com/in/bhavin-baldota-103553234/)
- GitHub: [@CoderFatherBB](https://github.com/CoderFatherBB)

---
<div align="center">
  <sub>Made with ❤️ by Bhavin Baldota</sub>
</div>
