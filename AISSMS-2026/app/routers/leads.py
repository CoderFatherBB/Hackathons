from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from app.core.db import get_db
from app.models.models import Lead, Call
from app.schemas.leads import LeadCreate, LeadResponse, LeadStatusUpdate
from app.tasks.outbound import call_lead
from app.core.config import settings
from app.services.twilio import initiate_call
import logging
logger = logging.getLogger("app.routers.leads")

router = APIRouter(prefix="/api/leads", tags=["leads"])

@router.post("/create", response_model=LeadResponse)
def create_lead(payload: LeadCreate, db: Session = Depends(get_db)):
    lead = Lead(name=payload.name, phone=payload.phone, source=payload.source)
    db.add(lead)
    db.commit()
    db.refresh(lead)
    if settings.twilio_from_number:
        print(f"[Leads] initiating call for lead={lead.id} to={lead.phone}")
        resp = initiate_call(lead.phone, settings.twilio_from_number)
        sid = resp.get("sid") if isinstance(resp, dict) else None
        if sid:
            print(f"[Leads] call sid received sid={sid}")
            call = Call(lead_id=lead.id, direction="outbound", call_sid=sid)
            db.add(call)
            db.commit()
        else:
            print(f"[Leads] direct call failed; enqueueing Celery task")
            call_lead.delay(lead.phone, settings.twilio_from_number)
    return LeadResponse(id=lead.id, name=lead.name, phone=lead.phone, source=lead.source, status=lead.status, score=lead.score)

@router.get("/{lead_id}", response_model=LeadResponse)
def get_lead(lead_id: UUID, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return LeadResponse(id=lead.id, name=lead.name, phone=lead.phone, source=lead.source, status=lead.status, score=lead.score)

@router.put("/update-status", response_model=LeadResponse)
def update_lead_status(payload: LeadStatusUpdate, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == payload.lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead.status = payload.status
    db.commit()
    db.refresh(lead)
    return LeadResponse(id=lead.id, name=lead.name, phone=lead.phone, source=lead.source, status=lead.status, score=lead.score)
