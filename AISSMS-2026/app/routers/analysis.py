from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from app.core.db import get_db
from app.models.models import Call, AgentScore, User
from app.schemas.analysis import UploadCallPayload, ScoreCallPayload, AgentScoreResult, AgentReport
from app.services.groq import score_agent

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

@router.post("/upload-call")
def upload_call(payload: UploadCallPayload, db: Session = Depends(get_db)):
    call = db.query(Call).filter(Call.id == payload.call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    call.recording_url = payload.s3_key
    db.commit()
    return {"status": "uploaded"}

@router.post("/score-call")
def score_call(payload: ScoreCallPayload, db: Session = Depends(get_db)):
    call = db.query(Call).filter(Call.id == payload.call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    raw = score_agent(payload.transcript)
    result = AgentScoreResult(**raw)
    total = (result.greeting_score + result.empathy_score + result.objection_score + result.closing_score + result.script_score) / 5.0
    score = AgentScore(agent_id=call.agent_id if call.agent_id else db.query(User).first().id if db.query(User).first() else None, call_id=call.id, greeting_score=result.greeting_score, empathy_score=result.empathy_score, objection_handling_score=result.objection_score, closing_score=result.closing_score, script_adherence_score=result.script_score, total_score=total, improvement_feedback=result.feedback)
    db.add(score)
    db.commit()
    return {"status": "scored"}

@router.get("/agent/{agent_id}/report", response_model=AgentReport)
def agent_report(agent_id: UUID, db: Session = Depends(get_db)):
    records = db.query(AgentScore).filter(AgentScore.agent_id == agent_id).all()
    if not records:
        return AgentReport(agent_id=agent_id, total_calls=0, average_score=0.0, recent_feedback=[])
    avg = sum(r.total_score for r in records) / len(records)
    feedbacks = [r.improvement_feedback for r in records if r.improvement_feedback][:10]
    return AgentReport(agent_id=agent_id, total_calls=len(records), average_score=avg, recent_feedback=feedbacks)
