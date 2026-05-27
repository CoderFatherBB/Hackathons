from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from uuid import UUID, uuid4
from app.core.db import get_db
from app.models.models import Call, Lead, User
from app.schemas.calls import InitiateOutboundCall, CallResponse
from app.services.memory import add_exchange, get_memory
from app.services.groq import classify_sales
from app.services.elevenlabs import synthesize
from app.core.config import settings
from app.services.twilio import initiate_call
import logging
logger = logging.getLogger("app.routers.calls")
from urllib.parse import parse_qs
from app.services.memory import client as redis_client

router = APIRouter(prefix="/api/calls", tags=["calls"])

@router.post("/initiate-outbound-call", response_model=CallResponse)
def initiate_outbound_call(payload: InitiateOutboundCall, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == payload.lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    agent = None
    if payload.agent_id:
        agent = db.query(User).filter(User.id == payload.agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
    call = Call(lead_id=lead.id, agent_id=agent.id if agent else None, direction="outbound")
    db.add(call)
    db.commit()
    db.refresh(call)
    if settings.twilio_from_number:
        print(f"[Calls] initiating outbound to={lead.phone} from={settings.twilio_from_number}")
        resp = initiate_call(lead.phone, settings.twilio_from_number)
        sid = resp.get("sid") if isinstance(resp, dict) else None
        if sid:
            call.call_sid = sid
            db.commit()
            print(f"[Calls] outbound sid={sid}")
    return CallResponse(call_id=call.id, lead_id=call.lead_id, direction=call.direction, call_sid=call.call_sid, escalation_flag=call.escalation_flag)

@router.post("/twilio-webhook")
async def twilio_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.form()
        call_sid = data.get("CallSid")
        from_number = data.get("From")
        to_number = data.get("To")
    except AssertionError:
        raw = await request.body()
        parsed = {k: v[0] for k, v in parse_qs(raw.decode()).items()}
        call_sid = parsed.get("CallSid")
        from_number = parsed.get("From")
        to_number = parsed.get("To")
    logger.info(f"twilio_webhook sid={call_sid} from={from_number} to={to_number}")
    print(f"[Webhook] sid={call_sid} from={from_number} to={to_number}")
    existing = db.query(Call).filter(Call.call_sid == call_sid).first() if call_sid else None
    if not existing:
        call = Call(direction="inbound", call_sid=call_sid)
        db.add(call)
        db.commit()
        db.refresh(call)
    add_exchange(call_sid or "", "system", "connected")
    greet = settings.voice_greeting_message
    audio_url = synthesize(greet)
    if audio_url:
        twiml = f'<?xml version="1.0" encoding="UTF-8"?><Response><Play>{audio_url}</Play><Gather input="speech" action="/api/calls/respond" method="POST" language="en-US" speechTimeout="auto" timeout="2" /></Response>'
    else:
        twiml = f'<?xml version="1.0" encoding="UTF-8"?><Response><Say>{greet}</Say><Gather input="speech" action="/api/calls/respond" method="POST" language="en-US" speechTimeout="auto" timeout="2" /></Response>'
    return Response(content=twiml, media_type="application/xml")

@router.get("/twilio-webhook")
def twilio_webhook_info():
    twiml = f'<?xml version="1.0" encoding="UTF-8"?><Response><Say>{settings.voice_greeting_message}</Say><Gather input="speech" action="/api/calls/respond" method="POST" language="en-US" speechTimeout="auto" timeout="2" /></Response>'
    return Response(content=twiml, media_type="application/xml")

@router.post("/recording-webhook")
async def recording_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.form()
        call_sid = data.get("CallSid")
        recording_url = data.get("RecordingUrl")
    except AssertionError:
        raw = await request.body()
        parsed = {k: v[0] for k, v in parse_qs(raw.decode()).items()}
        call_sid = parsed.get("CallSid")
        recording_url = parsed.get("RecordingUrl")
    logger.info(f"recording_webhook sid={call_sid} url={recording_url}")
    print(f"[Recording] sid={call_sid} url={recording_url}")
    call = db.query(Call).filter(Call.call_sid == call_sid).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    call.recording_url = recording_url
    db.commit()
    add_exchange(call_sid or "", "customer", f"recording:{recording_url}")
    result = classify_sales("")
    call.escalation_flag = bool(result.get("needs_escalation"))
    db.commit()
    twiml = '<?xml version="1.0" encoding="UTF-8"?><Response><Say>Thank you. Goodbye.</Say></Response>'
    return Response(content=twiml, media_type="application/xml")

@router.get("/audio/{key}.mp3")
def get_audio(key: str):
    data = redis_client.get(f"audio:{key}")
    if not data:
        raise HTTPException(status_code=404, detail="Audio not found")
    return Response(content=data, media_type="audio/mpeg")

@router.post("/respond")
async def respond(request: Request):
    try:
        data = await request.form()
        call_sid = data.get("CallSid")
        speech = data.get("SpeechResult") or data.get("Digits") or ""
    except AssertionError:
        raw = await request.body()
        parsed = {k: v[0] for k, v in parse_qs(raw.decode()).items()}
        call_sid = parsed.get("CallSid")
        speech = parsed.get("SpeechResult") or parsed.get("Digits") or ""
    add_exchange(call_sid or "", "customer", speech or "")
    mem = get_memory(call_sid or "")
    context = " ".join([m.get("content", "") for m in mem])
    from app.utils.llm import get_llm_response
    reply = get_llm_response(f"{context}\nUser: {speech}\nAssistant:")
    add_exchange(call_sid or "", "ai", reply or "")
    audio_url = synthesize(reply or "Thank you")
    if audio_url:
        twiml = f'<?xml version="1.0" encoding="UTF-8"?><Response><Play>{audio_url}</Play><Gather input="speech" action="/api/calls/respond" method="POST" language="en-US" speechTimeout="auto" timeout="2" /></Response>'
    else:
        twiml = f'<?xml version="1.0" encoding="UTF-8"?><Response><Say>{reply}</Say><Gather input="speech" action="/api/calls/respond" method="POST" language="en-US" speechTimeout="auto" timeout="2" /></Response>'
    return Response(content=twiml, media_type="application/xml")

@router.get("/{call_id}", response_model=CallResponse)
def get_call(call_id: UUID, db: Session = Depends(get_db)):
    call = db.query(Call).filter(Call.id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    return CallResponse(call_id=call.id, lead_id=call.lead_id, direction=call.direction, call_sid=call.call_sid, escalation_flag=call.escalation_flag)
