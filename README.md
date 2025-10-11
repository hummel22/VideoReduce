# VideoReduce

VideoReduce is an Android application paired with a lightweight desktop service that transcodes large video files into smaller, high-quality versions. The platform preserves original media until each conversion is verified and supports elevated quality profiles for selected files.

## System Overview

- **Android app** – Queues videos for processing, tracks conversion status, and stores metadata in a local SQLite database.
- **Processing service** – Runs on a user-managed computer. It watches an SMB share for new jobs, performs the video transcode (e.g., via HandBrake CLI or FFmpeg), and writes converted outputs back to the share.
- **Shared storage** – Two SMB directories coordinate hand-offs:
  - `/input` for originals written by the Android app.
  - `/output` for processed videos produced by the service.
  The app only purges originals after the user confirms the output is acceptable.

## Database and Migrations

All application state is stored in SQLite. Any change to the schema must include a forward-only migration so upgraded installations migrate automatically without wiping data. Migrations should be idempotent and versioned.

## Configurable Encoding Profiles

Administrators can tune output settings based on:

- Source file size ranges
- Video length buckets
- Source resolution tiers

Each rule maps to transcoding parameters such as bitrate, CRF, preset, and container format. Files flagged for "extra high quality" should use a dedicated profile.

## Running the Processing Service (Docker)

1. **Prerequisites**
   - Docker Engine 24+
   - Access to the SMB share that the Android app writes to
   - Optional: GPU drivers if hardware acceleration is desired

2. **Directory Layout**
   ```
   /srv/video-reduce/
     ├── config/               # YAML file with SMB paths and encoding profiles
     ├── jobs/input/           # Mounted to SMB input share
     └── jobs/output/          # Mounted to SMB output share
   ```

3. **Configuration File**

   Create `config/service.yml` with values similar to:
   ```yaml
   smb:
     input: "//HOST/VideoReduce/input"
     output: "//HOST/VideoReduce/output"
     username: "${SMB_USERNAME}"
     password: "${SMB_PASSWORD}"
   queue:
     poll_interval_seconds: 30
   encoding_profiles:
     default:
       tool: "handbrake"
       video_codec: "H.265"
       audio_codec: "aac"
       quality_target: "crf23"
     high_quality:
       inherits: "default"
       quality_target: "crf20"
   rules:
     - match:
         min_size_mb: 0
         max_size_mb: 500
         max_duration_minutes: 20
       profile: "default"
     - match:
         min_size_mb: 500
         max_duration_minutes: 120
       profile: "high_quality"
   ```

4. **Docker Compose**

   Create `docker-compose.yml` in `/srv/video-reduce`:
   ```yaml
   services:
     video-reduce-service:
       image: videoreduce/service:latest
       build: .
       restart: unless-stopped
       environment:
         - SMB_USERNAME=${SMB_USERNAME}
         - SMB_PASSWORD=${SMB_PASSWORD}
       volumes:
         - ./config/service.yml:/app/config/service.yml:ro
         - ./jobs/input:/app/input
         - ./jobs/output:/app/output
       devices:
         - /dev/dri:/dev/dri  # optional for VAAPI/QuickSync
   ```

5. **Build and Start**

   ```bash
   docker compose build
   docker compose up -d
   ```

6. **Monitoring**

   - View logs: `docker compose logs -f`
   - Check queue status: `docker compose exec video-reduce-service python manage.py queue:list`
   - Trigger manual retry: `docker compose exec video-reduce-service python manage.py queue:retry --job-id <ID>`

## Development Notes

- Store queue metadata, transcoding history, and SMB credentials (encrypted where possible) in SQLite tables with versioned migrations.
- Integrate HandBrakeCLI or FFmpeg adapters that map profile rules to actual command-line options.
- Ensure the Android app surfaces the queue status, allows "extra high quality" tagging, and requests user confirmation before deleting originals.

For further contributions, consult `AGENTS.md` for repository-wide guidance.
