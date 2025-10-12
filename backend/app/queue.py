"""Queue worker that monitors manifests and orchestrates HandBrakeCLI transcoding."""
from __future__ import annotations

import json
import shutil
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from .config import get_settings
from .database import SessionLocal
from .encoding import EncodingEngine
from .models import JobEvent, QueueJob, QueueStage

settings = get_settings()


class QueueWorker:
    """Background worker that polls for new jobs and processes them sequentially."""

    def __init__(self, poll_interval: int = settings.poll_interval_seconds):
        self.poll_interval = poll_interval
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the queue worker thread if it is not already running."""

        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, name="queue-worker", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Signal the worker to stop and wait for completion."""

        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            with SessionLocal() as session:
                self._scan_for_manifests(session)
                self._process_next_job(session)
                session.commit()
            time.sleep(self.poll_interval)

    def _scan_for_manifests(self, session: Session) -> None:
        """Create queue jobs for manifests discovered in the input directory."""

        for manifest_path in Path(settings.input_dir).glob("*.json"):
            try:
                with manifest_path.open("r", encoding="utf-8") as handle:
                    payload = json.load(handle)
            except (OSError, json.JSONDecodeError):
                continue
            video_name = payload.get("video_name")
            if not video_name:
                continue
            existing = (
                session.query(QueueJob)
                .filter(QueueJob.video_name == video_name)
                .one_or_none()
            )
            if existing:
                continue
            source_path = Path(settings.input_dir) / payload.get("source_file", video_name)
            if not source_path.exists():
                continue
            job = QueueJob(
                video_name=video_name,
                source_path=str(source_path),
                manifest_path=str(manifest_path),
                requested_profile=payload.get("profile"),
                high_quality=bool(payload.get("high_quality", False)),
                file_size_mb=payload.get("file_size_mb"),
                duration_seconds=payload.get("duration_seconds"),
                resolution_height=payload.get("resolution_height"),
            )
            session.add(job)
            session.add(
                JobEvent(job=job, event_type="queued", message="Discovered manifest"),
            )

    def _process_next_job(self, session: Session) -> None:
        job = (
            session.query(QueueJob)
            .filter(QueueJob.status == "queued")
            .order_by(QueueJob.created_at)
            .first()
        )
        if not job:
            return
        engine = EncodingEngine(session)
        try:
            evaluated = engine.select_profile(job)
            job.actual_profile = evaluated.profile
            job.status = "processing"
            job.stage = QueueStage.TRANSCODING.value
            job.started_at = datetime.utcnow()
            session.add(
                JobEvent(
                    job=job,
                    event_type="profile",
                    message=f"Using profile {evaluated.profile.name} ({evaluated.reason})",
                )
            )
            session.flush()
            self._run_transcode(session, job, evaluated.profile)
            job.progress = 100.0
            job.stage = QueueStage.COMPLETE.value
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            session.add(JobEvent(job=job, event_type="completed", message="Transcode finished"))
        except Exception as exc:  # pragma: no cover - runtime safeguard
            job.status = "failed"
            job.stage = QueueStage.FAILED.value
            job.error_message = str(exc)
            session.add(JobEvent(job=job, event_type="error", message=str(exc)))

    def _run_transcode(self, session: Session, job: QueueJob, profile) -> None:
        """Execute HandBrakeCLI for the supplied job and update progress."""

        handbrake = shutil.which(settings.handbrake_cli_path) or settings.handbrake_cli_path
        output_dir = Path(settings.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{Path(job.video_name).stem}_transcoded.mp4"
        command = [
            handbrake,
            "-i",
            job.source_path,
            "-o",
            str(output_file),
            "-e",
            profile.video_codec,
            "-E",
            profile.audio_codec,
            "-q",
            profile.quality_target.replace("crf", ""),
        ]
        if profile.preset:
            command.extend(["--preset", profile.preset])
        if profile.container:
            command.extend(["--format", profile.container])
        process = subprocess.Popen(  # noqa: S603,S607 - command constructed from trusted config
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert process.stdout is not None
        next_update = 0.0
        for line in process.stdout:
            percent = _parse_handbrake_progress(line)
            if percent is None:
                continue
            if percent >= next_update:
                next_update = percent + 2
                _update_progress(job, percent)
                session.add(job)
                session.commit()
        process.wait()
        if process.returncode != 0:
            raise RuntimeError(f"HandBrakeCLI exited with {process.returncode}")


def _parse_handbrake_progress(output_line: str) -> Optional[float]:
    """Attempt to parse the HandBrakeCLI progress percentage from an output line."""

    marker = "%"
    if marker not in output_line:
        return None
    try:
        percent = float(output_line.split(marker)[0].split()[-1])
    except (ValueError, IndexError):
        return None
    return max(0.0, min(100.0, percent))


def _update_progress(job: QueueJob, percent: float) -> None:
    """Update in-memory job progress. Persisting is deferred to the caller's session."""

    rounded = round(percent / 2) * 2
    job.progress = max(0.0, min(100.0, float(rounded)))
    job.updated_at = datetime.utcnow()
