"""SQLAlchemy ORM models for the VideoReduce backend."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class UserRole(str, Enum):
    """Enumerates supported user roles."""

    ADMIN = "admin"
    MOBILE = "mobile"


class QueueStage(str, Enum):
    """Represents the major stages for queue processing."""

    PENDING = "pending"
    TRANSCODING = "transcoding"
    UPLOAD = "upload"
    DOWNLOAD = "download"
    COMPLETE = "complete"
    FAILED = "failed"


class User(Base):
    """Application user capable of authenticating with the backend."""

    __tablename__ = "users"

    id: int = Column(Integer, primary_key=True)
    username: str = Column(String(255), unique=True, nullable=False)
    password: str = Column(String(255), nullable=False)
    role: str = Column(String(32), nullable=False, default=UserRole.MOBILE.value)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: datetime = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    tokens = relationship("APIToken", back_populates="user", cascade="all, delete-orphan")


class APIToken(Base):
    """API tokens used by the mobile client to authenticate."""

    __tablename__ = "api_tokens"

    id: int = Column(Integer, primary_key=True)
    token: str = Column(String(255), unique=True, nullable=False)
    description: Optional[str] = Column(String(255))
    user_id: int = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_used_at: Optional[datetime] = Column(DateTime)

    user = relationship("User", back_populates="tokens")


class SMBConfig(Base):
    """Stores SMB configuration returned to clients."""

    __tablename__ = "smb_config"

    id: int = Column(Integer, primary_key=True)
    input_path: str = Column(String(1024), nullable=False)
    output_path: str = Column(String(1024), nullable=False)
    share_url: str = Column(String(1024), nullable=False)
    username: str = Column(String(255), nullable=False)
    password: str = Column(String(255), nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: datetime = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class SMBPreset(Base):
    """Reusable SMB configuration templates for administrators."""

    __tablename__ = "smb_presets"

    id: int = Column(Integer, primary_key=True)
    name: str = Column(String(255), nullable=False)
    description: Optional[str] = Column(Text)
    share_url: str = Column(String(1024), nullable=False)
    username: str = Column(String(255), nullable=False)
    password: str = Column(String(255), nullable=False)
    input_path: str = Column(String(1024), nullable=False)
    output_path: str = Column(String(1024), nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: datetime = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class EncodingProfile(Base):
    """Reusable encoding settings for transcoding jobs."""

    __tablename__ = "encoding_profiles"

    id: int = Column(Integer, primary_key=True)
    name: str = Column(String(255), nullable=False, unique=True)
    tool: str = Column(String(50), nullable=False, default="handbrake")
    video_codec: str = Column(String(50), nullable=False)
    audio_codec: str = Column(String(50), nullable=False)
    quality_target: str = Column(String(50), nullable=False)
    preset: Optional[str] = Column(String(50))
    container: Optional[str] = Column(String(50))
    inherits_profile_id: Optional[int] = Column(Integer, ForeignKey("encoding_profiles.id"))
    is_high_quality: bool = Column(Boolean, default=False, nullable=False)

    parent = relationship("EncodingProfile", remote_side=[id])


class EncodingRule(Base):
    """Rule describing when a profile should be applied."""

    __tablename__ = "encoding_rules"

    id: int = Column(Integer, primary_key=True)
    name: str = Column(String(255), nullable=False)
    min_size_mb: Optional[float] = Column(Float)
    max_size_mb: Optional[float] = Column(Float)
    min_duration_seconds: Optional[int] = Column(Integer)
    max_duration_seconds: Optional[int] = Column(Integer)
    min_resolution_height: Optional[int] = Column(Integer)
    max_resolution_height: Optional[int] = Column(Integer)
    profile_id: int = Column(Integer, ForeignKey("encoding_profiles.id"), nullable=False)
    high_quality_only: bool = Column(Boolean, default=False, nullable=False)

    profile = relationship("EncodingProfile")


class QueueJob(Base):
    """Represents a queued transcoding job."""

    __tablename__ = "queue_jobs"
    __table_args__ = (UniqueConstraint("video_name", name="uq_queue_jobs_video_name"),)

    id: int = Column(Integer, primary_key=True)
    video_name: str = Column(String(255), nullable=False)
    source_path: str = Column(String(1024), nullable=False)
    manifest_path: str = Column(String(1024), nullable=False)
    status: str = Column(String(50), nullable=False, default="queued")
    stage: str = Column(String(50), nullable=False, default=QueueStage.PENDING.value)
    progress: float = Column(Float, nullable=False, default=0.0)
    requested_profile: Optional[str] = Column(String(255))
    actual_profile_id: Optional[int] = Column(Integer, ForeignKey("encoding_profiles.id"))
    high_quality: bool = Column(Boolean, default=False, nullable=False)
    file_size_mb: Optional[float] = Column(Float)
    duration_seconds: Optional[int] = Column(Integer)
    resolution_height: Optional[int] = Column(Integer)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: datetime = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    started_at: Optional[datetime] = Column(DateTime)
    completed_at: Optional[datetime] = Column(DateTime)
    error_message: Optional[str] = Column(Text)

    actual_profile = relationship("EncodingProfile")
    events = relationship("JobEvent", back_populates="job", cascade="all, delete-orphan")


class JobEvent(Base):
    """Audit log of queue job lifecycle events."""

    __tablename__ = "job_events"

    id: int = Column(Integer, primary_key=True)
    job_id: int = Column(Integer, ForeignKey("queue_jobs.id"), nullable=False)
    event_type: str = Column(String(50), nullable=False)
    message: str = Column(Text, nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)

    job = relationship("QueueJob", back_populates="events")


class DashboardSnapshot(Base):
    """Time-series snapshot of dashboard metrics."""

    __tablename__ = "dashboard_snapshots"

    id: int = Column(Integer, primary_key=True)
    active_jobs: int = Column(Integer, nullable=False, default=0)
    average_throughput_minutes: float = Column(Float, nullable=False, default=0.0)
    smb_latency_ms: float = Column(Float, nullable=False, default=0.0)
    storage_budget_bytes: int = Column(Integer, nullable=False, default=0)
    recorded_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)


class DashboardEvent(Base):
    """Narrative events displayed on the dashboard timeline."""

    __tablename__ = "dashboard_events"

    id: int = Column(Integer, primary_key=True)
    title: str = Column(String(255), nullable=False)
    description: str = Column(Text, nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
