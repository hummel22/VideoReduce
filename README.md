# VideoReduce

VideoReduce is an Android application paired with a lightweight backend service that transcodes large video files into smaller, high-quality versions. The platform preserves original media until each conversion is verified and supports elevated quality profiles for selected files. Both the mobile client and the backend dashboard work together to orchestrate SMB-based transfers, track transcoding progress, and manage reusable encoding portfolios.

## System Overview

- **Android app** – Authenticates against the backend, discovers local video files, applies filtering tools, and queues selected clips with a chosen or newly created transcode portfolio. It uploads originals to the configured SMB share, writes `<video_file_name>.json` job descriptors, and surfaces progress for uploads, transcodes, and downloads.
- **Backend service & dashboard** – Provides REST APIs for authentication, configuration, and progress reporting. Administrators manage SMB credentials, transcode portfolios, and user accounts through a Vue-based dashboard. The service watches queue activity, stores history in SQLite, and exposes per-file progress by video name for the mobile client.
- **Backend automation** – Ships with tooling to simplify local onboarding and production deployment. A `setup_backend.sh` helper script provisions a Python virtual environment, installs backend dependencies, applies database migrations, and launches the service. Containerized workflows are supported through a maintained `Dockerfile` and `docker-compose.yml` pair that can build and run the backend with a single command.
- **Shared storage** – Two SMB directories coordinate hand-offs:
  - `/input` for originals written by the Android app.
  - `/output` for processed videos produced by the service.
  The app only purges originals after the user confirms the output is acceptable.

## Android Application Experience

1. **Login & Configuration**
   - Authenticates with the backend to obtain session credentials.
   - Fetches a configuration payload that describes SMB share details (URL, username, password) plus input and output directory paths.

2. **Video Discovery & Selection**
   - Scans the device for video content and surfaces results with modern Material UI components.
   - Provides filters for size range, resolution, and video length to refine the selection.
   - Supports selecting individual files or choosing all results before queuing.

3. **Queueing Jobs**
   - Presents a modal to choose an existing transcode portfolio or create a new one when the user taps **Queue**.
   - Uploads each selected file to the SMB input directory and writes a matching JSON manifest describing the requested portfolio.

4. **Monitoring Progress**
   - Displays per-file progress bars that reflect upload, transcode, or download percentages, depending on the active stage.
   - Offers dedicated views for in-progress jobs, completed items, and items awaiting review.

5. **Review & Approval**
   - Allows side-by-side viewing of the original and transcoded outputs along with the applied settings.
   - Users can accept the transcode (with a confirmation warning that the original will be deleted), re-run with new settings, or keep both versions.

## Database and Migrations

All application state is stored in SQLite. Any change to the schema must include a forward-only migration so upgraded installations migrate automatically without wiping data. Migrations should be idempotent and versioned.

## Configurable Encoding Profiles

Administrators can tune output settings based on:

- Source file size ranges
- Video length buckets
- Source resolution tiers

Each rule maps to transcoding parameters such as bitrate, CRF, preset, and container format. Files flagged for "extra high quality" should use a dedicated profile.

## Backend Service & Dashboard

- Built with Vue for the administrative dashboard and backed by APIs that service the Android client.
- Supports user management, SMB configuration, transcode portfolio definitions, and queue monitoring.
- Persists queue history, user configuration, and run metadata in SQLite for later review.
- Exposes endpoints that return real-time transcode progress keyed by video file name for the mobile app.
- Provides a `setup_backend.sh` bootstrap script that:
  1. Creates or reuses a Python virtual environment in `.venv/`.
  2. Installs backend requirements from `requirements.txt` (or `pyproject.toml` where applicable).
  3. Executes database migrations and seeding commands.
  4. Starts the API server and the job processor with sensible defaults.
- Includes a `Dockerfile` and `docker-compose.yml` so the full stack can be built and run with:
  ```bash
  docker compose build
  docker compose up -d
  ```
  Mount the SMB input and output shares into the container to ensure queue processing works end-to-end.

### Administrative Dashboard

- The FastAPI backend serves an embedded Vue 3 + PrimeVue admin panel from [`/admin`](http://localhost:8000/admin).
- Static assets live under `backend/app/admin_ui/` and are mounted automatically when the service starts.
- The panel supports administrator login, issuing mobile API tokens, and revoking existing tokens. It communicates with the `/auth/login` and `/admin/tokens` endpoints using the same JWT workflow as other clients.
- Because the UI is bundled with CDN modules, no extra Node.js build step is required. Updates to `app.js` and `styles.css` are picked up immediately after reloading the page.
- When iterating on the dashboard, run the FastAPI app (`uvicorn backend.app.main:app --reload`) and ensure the `/admin` route renders without console errors in the browser. Automated verification is available via `pytest backend/tests/test_admin_ui.py`.

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
   - Inspect queue state: `curl http://localhost:8000/queue/jobs`

## Backend Development Quickstart

The backend lives under `backend/` and is implemented with FastAPI, SQLAlchemy, and HandBrakeCLI integration. Follow the steps
below to bootstrap a local environment that mirrors the production container.

### Prerequisites

- Python 3.11+
- HandBrakeCLI available on your `PATH`
- SQLite 3 (bundled with Python)

### Required Environment Variables

The service reads configuration from variables prefixed with `VIDEOR_`:

- `VIDEOR_ADMIN_USERNAME` – dashboard login username.
- `VIDEOR_ADMIN_PASSWORD` – dashboard login password.
- `VIDEOR_JWT_SECRET_KEY` – signing secret for issued JWTs.
- `VIDEOR_DATABASE_URL` – optional SQLAlchemy URL (defaults to `sqlite:///data/videoreduce.db`).
- `VIDEOR_INPUT_DIR` / `VIDEOR_OUTPUT_DIR` – optional overrides for the queue directories.

### Local Setup

```bash
./setup_backend.sh
```

The script creates `.venv/`, installs dependencies, applies SQLite migrations, and starts `uvicorn` with the queue worker.
Logs are written to `/tmp/videoreduce-api.log`.

### Running Tests

```bash
source .venv/bin/activate
pytest backend/tests
```

### Container Workflow

```bash
docker compose build
docker compose up -d
```

Mount your SMB input/output shares into `data/input` and `data/output` respectively so the queue worker can pick up manifests
and place transcoded files where downstream systems expect them.

## Android Development & Build Workflow

1. **Prerequisites**
   - Android Studio Giraffe or newer with the Android Gradle Plugin matching the repository configuration.
   - JDK 17 (bundled with Android Studio) and Android SDK platforms/Google USB drivers for device testing.

2. **Local Development**
   - Clone the repository and open the `android/` module in Android Studio.
   - Sync Gradle (`File > Sync Project with Gradle Files`) to download dependencies and verify build variants.
   - Use the **VideoReduceDebug** run configuration to install and debug on a connected device or emulator. Ensure the device can reach the backend API specified in the configuration payload.

3. **Building APKs**
   - **Debug APK**: `./gradlew assembleDebug` produces `android/app/build/outputs/apk/debug/app-debug.apk` for sideloading.
   - **Release APK**:
     1. Configure signing credentials in `android/gradle.properties` or via Android Studio's **Build > Generate Signed Bundle / APK** wizard.
     2. Run `./gradlew assembleRelease` to emit `android/app/build/outputs/apk/release/app-release.apk`.
     3. Upload the release APK to your distribution channel or sideload on test devices.

4. **Testing & QA**
   - Execute `./gradlew testDebugUnitTest` for JVM unit tests and `./gradlew connectedDebugAndroidTest` for instrumentation tests (requires a device or emulator).
   - Validate upload/transcode/download progress flows against a staging backend before promoting builds.

## Development Notes

- Store queue metadata, transcoding history, and SMB credentials (encrypted where possible) in SQLite tables with versioned migrations.
- Integrate HandBrakeCLI or FFmpeg adapters that map profile rules to actual command-line options.
- Ensure the Android app surfaces the queue status, allows "extra high quality" tagging, and requests user confirmation before deleting originals.

For further contributions, consult `AGENTS.md` for repository-wide guidance.
