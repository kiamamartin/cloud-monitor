import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)
    role = Column(String(50), default="user")
    created_at = Column(DateTime(timezone=True), default=utc_now)
    
    monitors = relationship("Monitor", back_populates="user", cascade="all, delete-orphan")

class Monitor(Base):
    __tablename__ = "monitors"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(255))
    url = Column(Text, nullable=False)
    method = Column(String(10), default="GET")
    interval_seconds = Column(Integer, default=30)
    timeout_ms = Column(Integer, default=5000)
    expected_status = Column(Integer, default=200)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    
    user = relationship("User", back_populates="monitors")
    results = relationship("MonitorResult", back_populates="monitor", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="monitor", cascade="all, delete-orphan")

class MonitorResult(Base):
    __tablename__ = "monitor_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    monitor_id = Column(UUID(as_uuid=True), ForeignKey("monitors.id"), nullable=False, index=True)
    status_code = Column(Integer, nullable=True)
    response_time_ms = Column(Float, nullable=True)
    is_up = Column(Boolean, nullable=False)
    checked_at = Column(DateTime(timezone=True), default=utc_now, index=True)
    
    monitor = relationship("Monitor", back_populates="results")

class Incident(Base):
    __tablename__ = "incidents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    monitor_id = Column(UUID(as_uuid=True), ForeignKey("monitors.id"), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), default=utc_now)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="OPEN") # OPEN or RESOLVED
    failure_reason = Column(Text, nullable=True)
    
    monitor = relationship("Monitor", back_populates="incidents")