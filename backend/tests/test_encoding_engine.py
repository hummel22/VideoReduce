"""Tests for the encoding profile selection engine."""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.encoding import EncodingEngine
from backend.app.models import Base, EncodingProfile, EncodingRule, QueueJob


def setup_database():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def test_selects_requested_profile():
    SessionLocal = setup_database()
    with SessionLocal() as session:
        profile = EncodingProfile(
            name="requested",
            tool="handbrake",
            video_codec="H.265",
            audio_codec="aac",
            quality_target="crf23",
        )
        session.add(profile)
        session.commit()
        job = QueueJob(video_name="sample.mp4", source_path="/tmp/sample.mp4", manifest_path="/tmp/sample.json")
        job.requested_profile = "requested"
        session.add(job)
        session.commit()
        engine = EncodingEngine(session)
        evaluated = engine.select_profile(job)
        assert evaluated.profile.name == "requested"


def test_selects_rule_profile():
    SessionLocal = setup_database()
    with SessionLocal() as session:
        default_profile = EncodingProfile(
            name="default",
            tool="handbrake",
            video_codec="H.265",
            audio_codec="aac",
            quality_target="crf23",
        )
        rule_profile = EncodingProfile(
            name="hq",
            tool="handbrake",
            video_codec="H.265",
            audio_codec="aac",
            quality_target="crf20",
        )
        session.add_all([default_profile, rule_profile])
        session.commit()
        rule = EncodingRule(name="large-files", min_size_mb=500, profile=rule_profile)
        session.add(rule)
        session.commit()
        job = QueueJob(
            video_name="big.mp4",
            source_path="/tmp/big.mp4",
            manifest_path="/tmp/big.json",
            file_size_mb=600,
        )
        session.add(job)
        session.commit()
        engine = EncodingEngine(session)
        evaluated = engine.select_profile(job)
        assert evaluated.profile.name == "hq"
