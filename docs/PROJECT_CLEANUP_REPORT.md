# KHUTA project cleanup report

Date: 2026-10-05

## Findings and classification

| Finding | Classification | Action |
|---|---|---|
| `backend/app/core/config.py` and `backend/migrations/env.py` | REQUIRED_APPLICATION_CODE | Retained and made the single `python-dotenv` configuration path authoritative for API and Alembic. |
| `db_config.py`, `load_to_db.py`, `load_stations.py`, `query_demo.py`, `test_connection.py` | REQUIRED_DEVELOPMENT_SCRIPT | Retained. The shared loader now reads ignored `backend/.env` through `python-dotenv`; no values are embedded. Ingestion scripts remain unchanged. |
| `backend/evaluation/evaluate_ai.py`, evaluation data/results, `backend/tests/**` | REQUIRED_DEVELOPMENT_SCRIPT | Retained. The database test now reads the configured URL through the app settings and remains opt-in. |
| `backend/migrations/versions/**` | REQUIRED_APPLICATION_CODE | Retained. Repository Alembic head is `0004_media_request_key`. |
| `add_grades.py` use of `ast.literal_eval` | REQUIRED_DEVELOPMENT_SCRIPT | Retained; it parses dataset values and does not inspect files for database credentials. |
| `backend/inspect_integration_db.py`, `backend/inspect_small.py`, `backend/run_migration.py`, `backend/run_db_tests_tmp.py` | TEMPORARY_CODEX_HELPER | Removed; none is imported by the application or required for Alembic. |
| Dummy URL defaults `user:password@localhost` and `USER:PASSWORD@HOST` | SECRET_OR_SECURITY_RISK | Removed from app defaults, Alembic config, and `.env.example`. These were placeholders, not live credentials, but could encourage unsafe fallback configuration. |
| `docs/RFID_INTEGRATION.md` reference to the “current Codex demo instance” | TEMPORARY_CODEX_HELPER | Removed; documentation now uses the project’s normal local development URL. |

No literal `C:\Users\...`, `Documents\Codex`, `inspect_existing.py`, or AST-based credential extraction reference was found in the readable KHUTA source/documentation scan. The `ast.literal_eval` dataset parser above is legitimate application-adjacent development code. No real API key or database password was found in the readable source files; secret values were not printed during the audit.

## Temporary files retained

- `backend/.venv/` is the local Python environment and is ignored by Git; it is retained for development.
- Empty `backend/pytest-cache-files-*` directories are test-run cache artifacts, not application files.
- `backend/.tmp/tmp_o_g3bua/` could not be inspected because Windows returned access denied. It was retained because its contents and purpose could not be verified safely; review or remove it manually if it is an obsolete local artifact.
- Evaluation reports/results, backups, migrations, tests, and ingestion scripts were retained as requested.

## Configuration and paths

- Application configuration: `backend/app/core/config.py` loads `backend/.env` (and a working-directory `.env`) with `python-dotenv`; explicit environment variables take precedence.
- Legacy psycopg development scripts: `db_config.py` loads `backend/.env` and reads `DATABASE_URL` from the environment.
- Alembic: `backend/migrations/env.py` calls the same settings layer. `backend/alembic.ini` no longer contains a database URL. No one-off migration runner is required.
- `backend/.gitignore` contains `.env`; `git check-ignore -v backend/.env` confirmed it is ignored.
- `.env.example` contains variable names and safe non-secret defaults only. `DATABASE_URL`, `OPENAI_API_KEY`, `ADMIN_API_KEY`, and `DEVICE_API_KEY` are blank. Embedding provider/model configuration is explicit.
- No machine-specific absolute path remains in the readable source/documentation scan. The environment-specific Codex demo wording was removed.

## Verification

- Backend startup: **passed**. Uvicorn started from the backend package without a database URL.
- Database health: **not connected**. `GET /health` returned HTTP 503 with `DATABASE_URL is not configured`; there is no `backend/.env` and no environment URL in this session. A passwordless connection attempt to the existing local endpoint also did not connect. No credentials were recovered from helper files.
- Alembic heads: **passed**, `0004_media_request_key (head)`.
- Alembic current: **not verifiable**. It stops with the explicit missing-`DATABASE_URL` message before connecting. The current database revision cannot be confirmed in this cleanup run.
- Automated tests: **29 passed, 1 skipped, 0 failed**. The settings test verifies environment-driven database and embedding configuration. The skipped test is the opt-in database integration test because no configured database URL is available.
- `public.passages`: last verified at **166,774** in the prior database integration run. This cleanup made no database connection capable of writes and changed no PostgreSQL data. The count could not be rechecked during this cleanup because `DATABASE_URL` is unavailable.
- Controlled station content: no database operations were performed; the previously verified 30 records were not changed.

## Remaining action

Create `backend/.env` locally from `.env.example` and set `DATABASE_URL` to the existing `islamic` database. Then rerun `alembic current`, the opt-in database integration test, and the health/count checks. The application does not need to parse a helper script or use a separate migration runner.
