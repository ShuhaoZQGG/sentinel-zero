"""Database models for SentinelZero."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .base import Base


class Process(Base):
    """Process model."""
    __tablename__ = "processes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    command = Column(Text, nullable=False)
    args = Column(JSON, default=list)
    working_dir = Column(Text)
    env_vars = Column(JSON, default=dict)
    status = Column(String(50), default="stopped", index=True)
    pid = Column(Integer)
    exit_code = Column(Integer)
    group_name = Column(String(255), index=True)
    restart_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime)
    stopped_at = Column(DateTime)
    
    # Relationships
    schedules = relationship("Schedule", back_populates="process", cascade="all, delete-orphan")
    logs = relationship("ProcessLog", back_populates="process", cascade="all, delete-orphan")
    metrics = relationship("Metric", back_populates="process", cascade="all, delete-orphan")
    restart_policy = relationship("RestartPolicyModel", back_populates="process", uselist=False)


class Schedule(Base):
    """Schedule model."""
    __tablename__ = "schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    process_id = Column(Integer, ForeignKey("processes.id"), nullable=False)
    name = Column(String(255), unique=True, nullable=False, index=True)
    schedule_type = Column(String(50), nullable=False)
    schedule_expr = Column(Text, nullable=False)
    enabled = Column(Boolean, default=True)
    last_run = Column(DateTime)
    next_run = Column(DateTime)
    run_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    process = relationship("Process", back_populates="schedules")


class RestartPolicyModel(Base):
    """Restart policy model."""
    __tablename__ = "restart_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    process_id = Column(Integer, ForeignKey("processes.id"), nullable=False, unique=True)
    policy_name = Column(String(255), nullable=False)
    max_retries = Column(Integer, default=3)
    retry_delay = Column(Integer, default=5)
    backoff_multiplier = Column(Float, default=1.5)
    max_delay = Column(Integer, default=300)
    restart_on_codes = Column(JSON)
    ignore_codes = Column(JSON)
    health_check_command = Column(Text)
    health_check_interval = Column(Integer, default=30)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Current restart state
    restart_count = Column(Integer, default=0)
    last_restart = Column(DateTime)
    consecutive_failures = Column(Integer, default=0)
    
    # Relationships
    process = relationship("Process", back_populates="restart_policy")


class ProcessLog(Base):
    """Process log model."""
    __tablename__ = "process_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    process_id = Column(Integer, ForeignKey("processes.id"), nullable=False)
    log_type = Column(String(50), nullable=False)  # stdout, stderr, system
    message = Column(Text)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    
    # Relationships
    process = relationship("Process", back_populates="logs")


class Metric(Base):
    """Process metrics model."""
    __tablename__ = "metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    process_id = Column(Integer, ForeignKey("processes.id"), nullable=False)
    cpu_percent = Column(Float)
    memory_mb = Column(Float)
    num_threads = Column(Integer)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    
    # Relationships
    process = relationship("Process", back_populates="metrics")