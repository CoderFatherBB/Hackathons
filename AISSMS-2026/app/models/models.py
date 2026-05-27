import uuid
from sqlalchemy import Column, String, DateTime, Enum, Float, Boolean, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped
from datetime import datetime, timezone
from app.core.db import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = Column(String(255), nullable=False)
    email: Mapped[str] = Column(String(255), unique=True, nullable=False)
    role: Mapped[str] = Column(Enum("admin", "agent", "supervisor", name="user_role"), nullable=False)
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    calls: Mapped[list] = relationship("Call", back_populates="agent")
    scores: Mapped[list] = relationship("AgentScore", back_populates="agent")

class Lead(Base):
    __tablename__ = "leads"
    id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = Column(String(255), nullable=False)
    phone: Mapped[str] = Column(String(32), nullable=False)
    source: Mapped[str] = Column(String(128), nullable=True)
    status: Mapped[str] = Column(Enum("new", "called", "hot", "warm", "cold", "converted", name="lead_status"), default="new", nullable=False)
    score: Mapped[float] = Column(Float, nullable=True)
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    calls: Mapped[list] = relationship("Call", back_populates="lead")

class Call(Base):
    __tablename__ = "calls"
    id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("leads.id"), nullable=True)
    agent_id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    direction: Mapped[str] = Column(Enum("inbound", "outbound", name="call_direction"), nullable=False)
    call_sid: Mapped[str] = Column(String(64), unique=True, nullable=True)
    recording_url: Mapped[str] = Column(Text, nullable=True)
    transcript: Mapped[str] = Column(Text, nullable=True)
    summary: Mapped[str] = Column(Text, nullable=True)
    sentiment_score: Mapped[float] = Column(Float, nullable=True)
    escalation_flag: Mapped[bool] = Column(Boolean, default=False, nullable=False)
    duration_seconds: Mapped[int] = Column(Integer, nullable=True)
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    lead: Mapped["Lead"] = relationship("Lead", back_populates="calls")
    agent: Mapped["User"] = relationship("User", back_populates="calls")
    messages: Mapped[list] = relationship("CallMessage", back_populates="call", cascade="all, delete-orphan")
    scores: Mapped[list] = relationship("AgentScore", back_populates="call")
    escalations: Mapped[list] = relationship("Escalation", back_populates="call")

class CallMessage(Base):
    __tablename__ = "call_messages"
    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    call_id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("calls.id"), nullable=False)
    speaker: Mapped[str] = Column(Enum("agent", "customer", "ai", name="speaker_type"), nullable=False)
    message_text: Mapped[str] = Column(Text, nullable=False)
    timestamp: Mapped[datetime] = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    call: Mapped["Call"] = relationship("Call", back_populates="messages")

class AgentScore(Base):
    __tablename__ = "agent_scores"
    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    agent_id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    call_id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("calls.id"), nullable=False)
    greeting_score: Mapped[int] = Column(Integer, nullable=False)
    empathy_score: Mapped[int] = Column(Integer, nullable=False)
    objection_handling_score: Mapped[int] = Column(Integer, nullable=False)
    closing_score: Mapped[int] = Column(Integer, nullable=False)
    script_adherence_score: Mapped[int] = Column(Integer, nullable=False)
    total_score: Mapped[float] = Column(Float, nullable=False)
    improvement_feedback: Mapped[str] = Column(Text, nullable=True)
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    agent: Mapped["User"] = relationship("User", back_populates="scores")
    call: Mapped["Call"] = relationship("Call", back_populates="scores")

class Escalation(Base):
    __tablename__ = "escalations"
    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    call_id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("calls.id"), nullable=False)
    escalated_to: Mapped[str] = Column(String(255), nullable=True)
    reason: Mapped[str] = Column(Text, nullable=True)
    resolved: Mapped[bool] = Column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    call: Mapped["Call"] = relationship("Call", back_populates="escalations")
