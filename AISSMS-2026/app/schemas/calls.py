from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class InitiateOutboundCall(BaseModel):
    lead_id: UUID
    agent_id: Optional[UUID] = None

class CallResponse(BaseModel):
    call_id: UUID
    lead_id: Optional[UUID] = None
    direction: str
    call_sid: Optional[str] = None
    escalation_flag: bool = False
