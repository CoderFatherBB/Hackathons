from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.models import Lead, AgentScore, User
from app.core.security import require_role

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/metrics")
def metrics(db: Session = Depends(get_db), _: None = Depends(require_role(["admin", "supervisor"]))):
    total_leads = db.query(Lead).count()
    converted = db.query(Lead).filter(Lead.status == "converted").count()
    total_calls_scored = db.query(AgentScore).count()
    return {"total_leads": total_leads, "converted_leads": converted, "total_calls_scored": total_calls_scored}

@router.get("/leaderboard")
def leaderboard(db: Session = Depends(get_db), _: None = Depends(require_role(["admin", "supervisor"]))):
    rows = db.query(User.name, AgentScore.total_score).join(AgentScore, AgentScore.agent_id == User.id).all()
    by_agent = {}
    for name, score in rows:
        by_agent.setdefault(name, []).append(score)
    leaderboard = [{"agent": k, "average_score": sum(v) / len(v)} for k, v in by_agent.items()]
    leaderboard.sort(key=lambda x: x["average_score"], reverse=True)
    return {"leaderboard": leaderboard}
