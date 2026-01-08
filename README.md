# DataMind — Natural Language to SQL Data Analytics Tool

DataMind is a full-stack system that allows users to query relational databases using **natural language** instead of SQL.  
It converts English queries into safe, read-only SQL, executes them on user-provided databases, and returns results with clear visualizations.

This project is built as a **modular, single FastAPI application** with a strong focus on:
- Clean architecture
- Security
- Explainability
- Separation of concerns

---

## Key Features

- Natural Language → SQL using a Transformer (T5)
- Schema-aware query generation
- Read-only, safe SQL execution
- Automatic result visualization
- Multi-user, multi-database support
- Clear engine-based architecture
- Offline model training, online inference only

---

##  System Architecture (High Level)

```
User
→ Auth & Session
→ Database Engine (schema + connection)
→ Preprocessing
→ Schema Linking
→ Schema Expansion
→ ML Model (NL → SQL)
→ SQL Validation
→ Execution
→ Visualization
→ User
```

- **FastAPI** acts only as an orchestrator
- All logic is encapsulated in internal engines
- Training and inference are strictly separated

---

##  Repository Structure

```
datamind/
├── app/                         # FastAPI application (runtime only)
├── training/                    # Offline model training scripts
├── models/                      # Frozen ML artifacts (T5)
├── docs/                        # Architecture & training docs
├── requirements.txt
├── README.md
└── DEVELOPER_GUIDELINES.md
```

---

##  Core Engines

| Engine | Responsibility |
|--------|----------------|
| Auth & Session | User authentication, session state |
| Database | DB connection, schema introspection |
| Preprocessing | Query normalization |
| Schema Linking | Map NL terms → schema candidates |
| Schema Expansion | Final schema & join selection |
| ML (Inference) | Generate SQL from NL |
| SQL Validation | Enforce safety & read-only rules |
| Execution | Run validated SQL |
| Visualization | Tables & charts |

**Each engine:**
- Has one responsibility
- Does not call other engines
- Is orchestrated by FastAPI

---

## Security Guarantees

- Only **SELECT** queries allowed
- No schema or data modification
- Single-statement SQL only
- Row and time limits enforced
- User databases are never stored
- Only metadata (schema) is cached

---

##  Machine Learning

- **Model:** T5 (Transformer)
- **Task:** Natural Language → SQL
- **Training:**
  - Performed offline (`/training`)
  - Uses datasets like WikiSQL / Spider
- **Inference:**
  - Performed inside FastAPI
  - Loads frozen artifacts from `/models`

> **Training code is never run in production.**

---

##  Running the Application

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Start FastAPI

```bash
uvicorn app.main:app --reload
```

### 3. Access API docs

```
http://localhost:8000/docs
```

---

##  Developer Notes

- Follow `DEVELOPER_GUIDELINES.md` strictly
- Do not introduce cross-engine imports
- Do not add logic to API routes
- Training and inference must remain separate

## Environment variables

Copy `.env.example` to `.env` and set the required values for local development and production.

- `AUTH_JWT_SECRET`: JWT signing secret (REPLACE with a strong secret in production).
- `AUTH_DB_URL`: SQLAlchemy DSN for auth users (defaults to `sqlite:///./auth_users.db` if unset). Example Postgres DSN: `postgresql+psycopg2://user:pass@host:5432/datamind_auth`.
- `REDIS_URL`: Optional Redis URL to enable Redis-backed sessions (if unset, sessions are in-memory).
- `APP_ENCRYPTION_KEY`: Fernet key (base64) to encrypt stored DB credentials. Generate with:

```bash
python - <<'PY'
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
PY
```

- `AUTH_JWT_EXP_SECONDS`: Optional token TTL in seconds (default `3600`).

## Local development checklist

1. Copy `.env.example` to `.env` and fill values.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. (Optional) Create a Postgres DB and set `AUTH_DB_URL` if you prefer Postgres for auth users.

4. Start the app:

```bash
uvicorn app.main:app --reload
```

5. Test the auth endpoints with curl or Postman:

```bash
# Signup
curl -X POST http://127.0.0.1:8000/auth/signup -H 'Content-Type: application/json' -d '{"email":"tester@example.com","password":"strong_password"}'

# Login
curl -X POST http://127.0.0.1:8000/auth/login -H 'Content-Type: application/json' -d '{"email":"tester@example.com","password":"strong_password"}'

# Use the returned access_token as Bearer for protected endpoints
```

6. Run unit tests:

```bash
pytest -q
```

---

##  Academic Context

This project is developed as part of a **B.Tech Computer Science & Engineering Major Project** and demonstrates:

- Applied NLP & Transformers
- Secure database interaction
- Modular backend architecture
- Practical ML system design

---

##  Disclaimer

This system is designed for **read-only analytics** and **educational purposes**.  
It is not intended for production database modification or unrestricted SQL access.

---

## Team

Developed by the **DataMind project team (VMASH)**  
- Haigovind M G
- Shreya Nair
- Vaishna T A
- Mariya K J
- Akhilkumar S

**Cochin University of Science and Technology (CUSAT)**
