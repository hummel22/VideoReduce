"""Pydantic schemas exposed via the API."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, constr

from .models import QueueStage, UserRole


class TokenResponse(BaseModel):
    """Represents a JWT session token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class LoginRequest(BaseModel):
    """Credentials payload for administrator authentication."""

    username: str
    password: str


class MobileTokenRequest(BaseModel):
    """Payload containing the mobile API token."""

    token: str


class SMBConfigResponse(BaseModel):
    """SMB configuration returned to clients."""

    input_path: str
    output_path: str
    share_url: str
    username: str
    password: str


class EncodingProfileBase(BaseModel):
    """Shared fields for encoding profiles."""

    id: int
    name: str
    tool: str
    video_codec: str
    audio_codec: str
    quality_target: str
    preset: Optional[str]
    container: Optional[str]
    inherits_profile_id: Optional[int]
    is_high_quality: bool

    class Config:
        orm_mode = True


class EncodingRuleResponse(BaseModel):
    """API representation of encoding rules."""

    id: int
    name: str
    min_size_mb: Optional[float]
    max_size_mb: Optional[float]
    min_duration_seconds: Optional[int]
    max_duration_seconds: Optional[int]
    min_resolution_height: Optional[int]
    max_resolution_height: Optional[int]
    profile: EncodingProfileBase
    high_quality_only: bool

    class Config:
        orm_mode = True


class QueueJobCreate(BaseModel):
    """Payload for queue job creation."""

    video_name: str
    requested_profile: Optional[str]
    high_quality: bool = False
    file_size_mb: Optional[float]
    duration_seconds: Optional[int]
    resolution_height: Optional[int]


class QueueJobResponse(BaseModel):
    """API representation of a queue job."""

    id: int
    video_name: str
    status: str
    stage: str
    progress: float
    requested_profile: Optional[str]
    actual_profile_id: Optional[int]
    high_quality: bool
    file_size_mb: Optional[float]
    duration_seconds: Optional[int]
    resolution_height: Optional[int]
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]

    class Config:
        orm_mode = True


class QueueProgressResponse(BaseModel):
    """Progress payload keyed by video name."""

    video_name: str
    progress: float = Field(ge=0, le=100)
    status: str
    stage: QueueStage


class JobEventResponse(BaseModel):
    """Represents an individual job event."""

    event_type: str
    message: str
    created_at: datetime

    class Config:
        orm_mode = True


class QueueJobDetailResponse(QueueJobResponse):
    """Extended queue job response with related data."""

    events: list[JobEventResponse]


class CreateTokenRequest(BaseModel):
    """Administrative request to create a new API token."""

    username: str
    description: Optional[str]


class CreateTokenResponse(BaseModel):
    """Response containing the issued API token."""

    token: str
    user_id: int
    description: Optional[str]


class UserResponse(BaseModel):
    """API representation of a user."""

    id: int
    username: str
    role: UserRole

    class Config:
        orm_mode = True


class TokenListResponse(BaseModel):
    """List of API tokens for administrative inspection."""

    id: int
    token: str
    description: Optional[str]
    user: UserResponse

    class Config:
        orm_mode = True


class DashboardSnapshotCreate(BaseModel):
    """Payload for recording dashboard analytics."""

    active_jobs: int = Field(default=0, ge=0)
    average_throughput_minutes: float = Field(default=0.0, ge=0)
    smb_latency_ms: float = Field(default=0.0, ge=0)
    storage_budget_bytes: int = Field(default=0, ge=0)


class DashboardSnapshotResponse(DashboardSnapshotCreate):
    """Dashboard metrics sample returned via the API."""

    id: Optional[int]
    recorded_at: datetime

    class Config:
        orm_mode = True


class DashboardEventCreate(BaseModel):
    """Payload describing a dashboard timeline event."""

    title: constr(min_length=1)
    description: constr(min_length=1)


class DashboardEventResponse(BaseModel):
    """Dashboard timeline event returned via the API."""

    id: int
    title: str
    description: str
    created_at: datetime

    class Config:
        orm_mode = True


class CreateUserRequest(BaseModel):
    """Request payload for provisioning a user API token."""

    username: constr(min_length=1)


class UserTokenResponse(BaseModel):
    """API token metadata used by the dashboard users panel."""

    id: int
    username: str
    token: str
    created_at: datetime


class CreateUserResponse(UserTokenResponse):
    """Response body when a new user token is created."""

    pass
