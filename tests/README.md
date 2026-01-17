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
