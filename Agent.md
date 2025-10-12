# Agent Expectations

- Keep `README.md` synchronized with any workflow, dependency, or UI changes.
- Plan and apply forward-only database migrations when modifying schemas; document manual steps when automated migrations are not feasible.
- Run the backend test suite and build commands that exercise the current change set, ensuring the service boots without startup errors before handing off work.
