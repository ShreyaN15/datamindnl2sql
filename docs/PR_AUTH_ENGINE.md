## PR: Auth & Session Engine Implementation — Summary of Changes

This document describes the proposed pull request that implements the Auth & Session engine, the files it changed or added, rationale for each change, testing steps, and reviewer guidance. Use this as the authoritative changelog for reviewers and maintainers.

---

### High-level summary

- Implemented a pure-Python Auth & Session engine that handles user identity, session lifecycle, and per-user DB connection metadata.
- Wired HTTP endpoints under `/auth/*` that call the engine (signup, login, logout, session/me, session/set-db).
- Added optional session persistence (Redis) and encryption for stored DB credentials (Fernet).
- Added unit tests and a small import-rule linter. A CI workflow was added for convenience (can be removed later if desired).

---

### Files added or modified in this PR

# PR: Auth & Session Engine — Long-form Summary & Integration Guide

This document is the single, canonical long-form PR body and integration guide for the Auth & Session engine. It combines the PR summary, rationale, testing instructions, integration guidance for other engines, reviewer checklist, and maintenance notes.

If you prefer the content split into multiple files, tell me which sections you'd like moved back into separate docs.

---

## TL;DR

- Implemented a pure-Python Auth & Session engine that handles user identity, session lifecycle, and storage of per-user DB connection metadata.
- Wired HTTP endpoints under `/auth/*` that call the engine (signup, login, logout, session/me, session/set-db).
- Added optional Redis-backed sessions and Fernet-based encryption for stored DB credentials.
- Added unit tests, a small import-rule linter, and optional CI workflow.

The engine is pure-Python (no FastAPI imports). The API layer is the orchestrator and performs authentication checks and passes sanitized session context or DB credentials into engines as explicit parameters.

---

## Files added or modified (complete list)

- Modified: `app/engines/auth/service.py`
	- Implements: `create_user`, `authenticate_user`, `create_session`, `get_session_context` (sanitised), `set_active_database`, `logout`, `verify_token`, `get_db_credentials`.
	- Features: lazy SQLAlchemy engine selection via `AUTH_DB_URL`, Redis sessions (`REDIS_URL`), optional Fernet encryption (`APP_ENCRYPTION_KEY`).

- Added: `app/engines/auth/_test_local.py`
	- Local pure-Python test runner (package-relative import). Tests the engine without FastAPI.

- Modified: `app/api/auth.py`
	- Orchestration endpoints: `POST /auth/signup`, `POST /auth/login`, `POST /auth/logout`, `GET /auth/session/me`, `POST /auth/session/set-db`.

- Modified: `app/api/query.py`
	- Added a small FastAPI dependency to require a Bearer token for `POST /query/` and to inject the sanitized session context into the handler. This is a minimal, intentional API-level change to enforce the guideline that queries require auth.

- Added: `app/core/security.py`
	- Fernet-based `encrypt_value` / `decrypt_value` helpers used by the auth engine.

- Added: `tests/test_auth_engine.py`
	- Pytest unit test covering the auth lifecycle (signup→login→set-db→logout).

- Added: `.env.example` and `README.md` updates
	- Document required env vars and local development steps.

- Added: `scripts/check_import_rules.py` (linter) and `.github/workflows/ci.yml` (CI)
	- These enforce import rules and run tests in GitHub Actions. They are optional and can be removed if you prefer not to run CI.

- Modified: `requirements.txt` (added `cryptography`)

---

## Why these changes were necessary

- The project requires engine isolation: engines are framework-agnostic, unit-testable modules that do not import FastAPI or other engines.
- Auth and session management must centralize user identity and per-user DB metadata so the orchestrator (API) can provide credentials safely to engines.
- DB credentials stored in-session should be encrypted at rest (Fernet) in production and persisted via Redis for distributed deployments.

---

## Authentication design (summary)

- Token type: JWT (signed with `AUTH_JWT_SECRET`). Token fields: `sub` (user id), `email`, `iat`, `exp`.
- Session store: token → session metadata (in-memory by default). Use Redis by setting `REDIS_URL`.
- Password hashing: `passlib` with `pbkdf2_sha256` for portability.
- DB credentials: if `APP_ENCRYPTION_KEY` is set, the password is encrypted with Fernet and stored as `password_enc` in the session; otherwise stored as `password` (not recommended for production).
- Session context exposure: `get_session_context(token)` returns a sanitized object without password fields. Raw credentials are available only through `get_db_credentials(token)` and should be used only by the orchestrator or a controlled database helper.

---

## Integration guide — how engines should use Auth & Sessions

The following patterns are required for engine authors and API implementers to maintain the project's architectural rules.

1. No engine→engine imports
	 - Engines must not import other engines (including `app.engines.auth`). If an engine needs data or credentials, the API layer must obtain them and pass them explicitly as parameters.

2. API layer is the orchestrator
	 - FastAPI route handlers perform authentication checks, permissions, and assemble inputs for engines. Engines accept explicit parameters and remain independent.

3. Session context is read-only to engines
	 - Engines receive a `session_context` (or relevant fields) and must treat it as read-only. Do not modify session objects inside engines.

4. Controlled credentials access
	 - Only code responsible for opening DB connections (API handlers or a platform-owned `database` helper) may call `auth_service.get_db_credentials(token)` to retrieve decrypted credentials. Engines must never call this function.

5. Passing credentials explicitly
	 - When an engine (e.g., `execution`) needs DB access, the API should retrieve credentials, open a short-lived connection via a `database` helper, and pass either the connection or a sanitized credential object into the engine function.

Example safe flow (API pseudo-code):

```py
token = extract_token(request)
auth_service.verify_token(token)
session = auth_service.get_session_context(token)
creds = auth_service.get_db_credentials(token)  # orchestrator only
conn = database_helper.connect(creds)
result = execution_engine.run_sql(conn, sql, session_context=session)
conn.close()
```

Rationale: keeps credential access centralized and preserves engine independence.

---

## Testing & verification steps for reviewers

1. Install requirements: `pip install -r requirements.txt`.
2. (Optional) Set env vars or use defaults from `.env.example`.
3. Run unit tests: `pytest -q` — all tests should pass.
4. Start the app: `uvicorn app.main:app --reload` and exercise endpoints using curl/Postman:
	 - `POST /auth/signup` — create a user
	 - `POST /auth/login` — returns JWT
	 - `GET /auth/session/me` — returns sanitized session
	 - `POST /auth/session/set-db` — store DB metadata (password encrypted if key is set)
	 - `POST /auth/logout` — invalidates session
5. Confirm `POST /query/` requires a Bearer token.

---

## Reviewer checklist

- [ ] Verify no engine file imports FastAPI.
- [ ] Verify there are no engine→engine imports.
- [ ] Ensure `get_session_context()` returns sanitized metadata (no `password` or `password_enc`).
- [ ] Confirm `get_db_credentials()` exists and is documented as a controlled internal API.
- [ ] Confirm unit tests pass locally and in CI (if CI enabled).
- [ ] Confirm README and `.env.example` updated with required env vars.

---



