# Agent Guidelines

## Scope
These instructions apply to the entire repository.

## General Development Practices
- Favor clear, modular Kotlin and Python code when adding automation scripts or Android components.
- Document public functions and non-trivial classes with KDoc or docstrings.
- When adding new configuration files, prefer YAML or JSON over custom formats unless there is a strong justification otherwise.

## Database Requirements
- The application state is persisted in a SQLite database.
- **Any schema change must ship with a forward-only migration** so that existing installations are upgraded automatically without deleting the database. Include regression tests or documented manual steps for migrations when possible.
- Migration scripts should be idempotent and guard against being re-run during incremental updates.

## Testing and Tooling
- Provide clear commands in documentation for running unit tests and background services.
- Validate that queue processing and storage layers behave correctly with both standard and high-quality video profiles when adding relevant tests.

## Documentation
- Keep README files up to date with any new setup steps, configuration options, or external service requirements.
- When touching docs, ensure references to the SMB transfer workflow remain accurate.
