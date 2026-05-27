from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID

class LeadCreate(BaseModel):
    name: str
    phone: str
    source: Optional[str] = None

class LeadResponse(BaseModel):
    id: UUID
    name: str
    phone: str
    source: Optional[str] = None
    status: str
    score: Optional[float] = None

class LeadStatusUpdate(BaseModel):
    lead_id: UUID
    status: str = Field(pattern="^(new|called|hot|warm|cold|converted)$")
