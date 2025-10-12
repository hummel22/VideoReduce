# Feature Requests and Delivery Order

## Development Order
1. **B1 – Backend Environment Automation**
2. **B2 – Backend Data Persistence & Migrations**
3. **B3 – Encoding Profile Engine & Tooling Integration**
4. **B4 – Core Backend APIs & SMB Configuration**
5. **B5 – Queue Processing & Progress Reporting**
6. **B6 – Vue Dashboard Administration Experience**
7. **M1 – Mobile Authentication & Configuration Sync**
8. **M2 – Mobile Video Discovery & Filtering**
9. **M3 – Mobile Queue Creation & Manifest Generation**
10. **M4 – Mobile Upload Orchestration & Progress Views**
11. **M5 – Mobile Review & Approval Workflow**
12. **M6 – Material Design Compliance & QA**

## Backend Feature Requests

### B1 – Backend Environment Automation
**Description:** Provide turnkey scripts and container assets so contributors can bootstrap and run the backend quickly.

**Required Tasks:**
- Implement `setup_backend.sh` to create or reuse a `.venv`, install Python dependencies, run migrations, and start the API/job services.
- Maintain a production-ready `Dockerfile` and `docker-compose.yml` that build, configure environment variables, and mount SMB shares for queue processing.
- Document usage patterns for both the shell script and Docker workflows, including prerequisites and monitoring commands.

### B2 – Backend Data Persistence & Migrations
**Description:** Establish reliable SQLite storage for configuration, queue metadata, history, and credentials.

**Required Tasks:**
- Design normalized SQLite schemas covering users, SMB configuration, encoding portfolios, queue jobs, run history, and credential storage with encryption where possible.
- Create forward-only, idempotent migration scripts and ensure `setup_backend.sh` executes them automatically.
- Implement automated or documented regression checks that validate migrations against existing databases.

### B3 – Encoding Profile Engine & Tooling Integration
**Description:** Manage configurable encoding rules and map them to transcoding tooling such as HandBrakeCLI or FFmpeg.

**Required Tasks:**
- Model encoding profiles with inheritance, bitrate/CRF/preset settings, and container formats based on README rules.
- Implement rule evaluation for size, duration, and resolution tiers, including “extra high quality” handling.
- Integrate transcoding tools that translate selected profiles into executable commands and support GPU acceleration when available.

### B4 – Core Backend APIs & SMB Configuration
**Description:** Expose REST endpoints that power the Android client’s authentication, configuration, and queue workflows.

**Required Tasks:**
- Implement authentication endpoints that issue session credentials for the mobile app.
- Provide configuration APIs returning SMB share URLs, credentials, and input/output directory paths.
- Deliver endpoints for queue submission metadata, per-file progress by video name, and history retrieval.
- Harden SMB credential management, ensuring secure storage and retrieval via the API.

### B5 – Queue Processing & Progress Reporting
**Description:** Orchestrate SMB-based file transfers, monitor transcodes, and publish status updates.

**Required Tasks:**
- Watch the SMB input directory for uploaded originals and associated `<video_file_name>.json` manifests.
- Execute transcoding jobs, write processed outputs to the SMB output directory, and preserve originals until approval.
- Track upload, transcode, and download stages with percentage updates exposed through the API.
- Record job lifecycle events and statuses in SQLite for future review and auditing.

### B6 – Vue Dashboard Administration Experience
**Description:** Build the Vue-based dashboard that allows administrators to manage the service and observe activity.

**Required Tasks:**
- Implement user management interfaces, including role assignment and credential resets.
- Provide SMB configuration panels to edit share URLs, usernames, and passwords with validation.
- Surface queue monitoring views that show in-progress jobs, their profiles, and current stages.
- Add history views for completed runs with filtering, retry triggers, and profile summaries.
- Offer UI to maintain transcode portfolios, including creation, cloning, and deletion workflows.

## Mobile App Feature Requests

### M1 – Mobile Authentication & Configuration Sync
**Description:** Enable the Android app to authenticate and retrieve backend configuration details during onboarding.

**Required Tasks:**
- Implement login screens that authenticate against the backend and persist session tokens securely.
- Fetch the configuration payload containing SMB share information, credentials, and directory paths after login.
- Validate connectivity to the SMB share using provided credentials and surface errors gracefully.

### M2 – Mobile Video Discovery & Filtering
**Description:** Discover device video files and provide tools to refine the selection.

**Required Tasks:**
- Scan local storage for video files, indexing metadata such as size, resolution, and duration.
- Build Material-compliant filtering controls for size ranges, resolutions, and video length ranges.
- Present results in a modern UI with options to select individual files or select all.

### M3 – Mobile Queue Creation & Manifest Generation
**Description:** Let users queue uploads with predefined or custom transcode portfolios and emit manifest files.

**Required Tasks:**
- Implement the queue action that opens a modal to choose an existing portfolio or create a new one.
- Collect user-selected transcode settings and store them alongside queued files.
- Support marking items for “extra high quality” processing when assembling queue entries.
- Generate `<video_file_name>.json` descriptors aligned with backend expectations and place them with the upload set.

### M4 – Mobile Upload Orchestration & Progress Views
**Description:** Handle SMB uploads in the background and keep users informed about status.

**Required Tasks:**
- Upload selected videos to the SMB input directory while monitoring transfer health and retries.
- Update per-file progress bars that indicate upload, transcode, and download percentages based on backend feedback.
- Provide dedicated screens for in-progress jobs and completed items, with pull-to-refresh or live updates.

### M5 – Mobile Review & Approval Workflow
**Description:** Support post-processing review, including comparisons and approval decisions.

**Required Tasks:**
- Present a review screen listing items awaiting action with access to originals and transcoded outputs.
- Render side-by-side playback with visible transcode settings and metadata.
- Allow users to accept (with confirmation acknowledging original deletion), rerun with new settings, or retain both versions.

### M6 – Material Design Compliance & QA
**Description:** Ensure the application adheres to modern Material Design patterns and maintains quality.

**Required Tasks:**
- Apply up-to-date Material components and theming across login, discovery, queue, progress, and review flows.
- Conduct manual and automated tests (`./gradlew testDebugUnitTest`, `./gradlew connectedDebugAndroidTest`) to validate flows against a staging backend.
- Perform UX reviews to confirm consistency, accessibility, and responsiveness across device sizes.
