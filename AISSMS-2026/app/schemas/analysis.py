from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID

class UploadCallPayload(BaseModel):
    call_id: UUID
    s3_key: str

class LLMSalesOutput(BaseModel):
    response_text: str
    lead_classification: str = Field(pattern="^(hot|warm|cold)$")
    intent_score: int = Field(ge=0, le=100)
    needs_escalation: bool

class ScoreCallPayload(BaseModel):
    call_id: UUID
    transcript: str

class AgentScoreResult(BaseModel):
    greeting_score: int = Field(ge=0, le=10)
    empathy_score: int = Field(ge=0, le=10)
    objection_score: int = Field(ge=0, le=10)
    closing_score: int = Field(ge=0, le=10)
    script_score: int = Field(ge=0, le=10)
    feedback: str

class AgentReport(BaseModel):
    agent_id: UUID
    total_calls: int
    average_score: float
    recent_feedback: List[str]
