"""Encoding profile evaluation utilities."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from .models import EncodingProfile, EncodingRule, QueueJob


@dataclass
class EvaluatedProfile:
    """Result of an encoding profile evaluation."""

    profile: EncodingProfile
    reason: str


class EncodingEngine:
    """Selects encoding profiles for queue jobs based on rules and metadata."""

    def __init__(self, session: Session):
        self.session = session

    def select_profile(self, job: QueueJob) -> EvaluatedProfile:
        """Determine the encoding profile for the supplied job."""

        if job.requested_profile:
            profile = (
                self.session.query(EncodingProfile)
                .filter(EncodingProfile.name == job.requested_profile)
                .one_or_none()
            )
            if profile:
                return EvaluatedProfile(profile=profile, reason="requested")
        rules = self.session.query(EncodingRule).all()
        for rule in rules:
            if self._matches_rule(rule, job):
                return EvaluatedProfile(profile=rule.profile, reason=f"rule:{rule.name}")
        fallback = (
            self.session.query(EncodingProfile)
            .filter(EncodingProfile.name == "default")
            .one_or_none()
        )
        if fallback is None:
            raise ValueError("No encoding profile available for job")
        return EvaluatedProfile(profile=fallback, reason="fallback")

    def _matches_rule(self, rule: EncodingRule, job: QueueJob) -> bool:
        """Return True when the job metadata satisfies the rule constraints."""

        if rule.high_quality_only and not job.high_quality:
            return False
        if rule.min_size_mb and job.file_size_mb and job.file_size_mb < rule.min_size_mb:
            return False
        if rule.max_size_mb and job.file_size_mb and job.file_size_mb > rule.max_size_mb:
            return False
        if (
            rule.min_duration_seconds
            and job.duration_seconds
            and job.duration_seconds < rule.min_duration_seconds
        ):
            return False
        if (
            rule.max_duration_seconds
            and job.duration_seconds
            and job.duration_seconds > rule.max_duration_seconds
        ):
            return False
        if (
            rule.min_resolution_height
            and job.resolution_height
            and job.resolution_height < rule.min_resolution_height
        ):
            return False
        if (
            rule.max_resolution_height
            and job.resolution_height
            and job.resolution_height > rule.max_resolution_height
        ):
            return False
        return True
