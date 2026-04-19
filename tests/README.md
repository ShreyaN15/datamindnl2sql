# Tests Directory

This directory contains all test files and migration scripts for DataMind NL2SQL.

## Test Files

### Schema Inference Tests

- `test_schema_inference.py` - SQLite schema inference test
- `test_postgres_schema.py` - PostgreSQL schema inference test (recommended)
- `setup_postgres_test.sql` - SQL script to create test database

### NL2SQL Tests

- `test_nl2sql.py` - Basic NL2SQL functionality test
- `test_nl2sql_postgres.py` - End-to-end NL2SQL test with PostgreSQL
- `test_nl2sql_output.txt` - Output from NL2SQL tests

### Other Tests

- `test_auth_db.py` - Authentication and database tests

### Migration Scripts

- `migrate_schema.py` - Database migration to add schema storage columns

## Endpoint regression (library / employee / student)

After code changes, run the **API-level** suite (creates a temp user, wires Postgres
connections, runs `/query/execute-sql` smoke queries, then `/query/nl2sql` with
`execute_query=true`). Pass/fail is based on **HTTP status** and
**`execution_result.success`**, not on matching generated SQL text.

```bash
cd /path/to/datamindnl2sql
source venv/bin/activate
pip install -r requirements-e2e.txt   # once: adds httpx for TestClient
python scripts/run_endpoint_regression_suite.py
```

Environment:

| Variable | Purpose |
|----------|---------|
| `SKIP_PG=1` | Skip Postgres (only registers user; for CI smoke) |
| `SKIP_NL2SQL=1` | After connections work, skip NL2SQL+model (execute-sql only) |
| `PG_E2E_HOST` / `PG_E2E_PORT` / `PG_E2E_USER` / `PG_E2E_PASSWORD` | Postgres for `library_db`, `employee_db`, `student_db` |

**Severity:** `required` cases must pass for exit code 0. `best_effort` (notably some
`student_db` joins) log warnings only — see `STUDENT_DB_INFO.txt` for known model limits.

Thin smoke (no Postgres): `python -m unittest tests.test_endpoint_regression_smoke`

## Running Tests

### Test Schema Inference (PostgreSQL - Recommended)

```bash
cd /Users/harismac/Desktop/datamindnl2sql
source venv/bin/activate
python tests/test_postgres_schema.py
```

Expected output:

- 6 tables detected
- 29 columns detected
- 6 foreign keys detected

### Test NL2SQL Pipeline

```bash
python tests/test_nl2sql_postgres.py
```

Tests 8 different query types from simple to complex.

### Setup Test Database

```bash
psql -U postgres -d postgres -f tests/setup_postgres_test.sql
```

Creates `datamind_test` database with sample e-commerce data.

## Test Database Schema

The test database includes:

- **users** (5 records)
- **categories** (3 records)
- **products** (10 records)
- **orders** (8 records)
- **order_items** (12 records)
- **reviews** (6 records)

With 6 foreign key relationships for testing JOIN queries.
