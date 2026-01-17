# DataMind — Natural Language to SQL Data Analytics Tool

DataMind is a full-stack system that allows users to query relational databases using **natural language** instead of SQL.  
It converts English queries into safe, read-only SQL, executes them on user-provided databases, and returns results with clear visualizations.

This project features:

- **Automatic schema inference** with multi-method foreign key detection
- **T5-based NL2SQL generation** with schema context
- **Clean web interface** built with Next.js
- **Production-ready architecture** with FastAPI backend

---

## 🚀 Quick Start

### One-Command Startup

```bash
./start.sh
```

This will:

- Kill any processes blocking ports 8000 and 3000
- Start the backend API on http://localhost:8000
- Start the frontend on http://localhost:3000
- Display logs and status

**To stop all services:**

```bash
./stop.sh
```

### Manual Startup

**Backend:**

```bash
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm run dev
```

---

## Key Features

- ✅ **Automatic Schema Inference** - Extracts tables, columns, and foreign keys automatically
- ✅ **Multi-Method FK Detection** - Explicit constraints + naming pattern inference
- ✅ **NL2SQL Generation** - T5 transformer model trained on Spider dataset
- ✅ **Schema-Aware Queries** - Model receives full schema context including relationships
- ✅ **Web Interface** - Modern React/Next.js UI with TypeScript
- ✅ **Multi-Database Support** - PostgreSQL, MySQL, SQLite
- ✅ **Authentication & Authorization** - Secure JWT-based auth
- ✅ **Real-Time Schema Refresh** - Update schema when database changes

---

## System Architecture

```
┌─────────────────┐
│   Next.js UI    │  Port 3000
│  (TypeScript)   │
└────────┬────────┘
         │ HTTP API
         │
┌────────▼────────┐
│  FastAPI Backend│  Port 8000
│   (Python)      │
└────┬────────┬───┘
     │        │
     │        └─────────────┐
     │                      │
┌────▼─────┐      ┌────────▼────────┐
│PostgreSQL│      │  T5 NL2SQL Model│
│  (User   │      │  (Transformer)  │
│   Data)  │      └─────────────────┘
└──────────┘
     │
     └──────────────┐
                    │
          ┌─────────▼────────┐
          │  Target Database │
          │  (PostgreSQL)    │
          └──────────────────┘
```

**Engine-based architecture:**

- Authentication Engine
- Database Connection Engine
- Schema Inference Engine
- Preprocessing Engine
- Schema Linking Engine
- ML Inference Engine
- SQL Validation Engine
- Execution Engine
- Visualization Engine

---

## Repository Structure

```
datamindnl2sql/
├── app/                         # FastAPI Backend
│   ├── api/                    # API endpoints (auth, db, query)
│   ├── core/                   # Core config & security
│   ├── db/                     # Database models & session
│   ├── engines/                # Business logic engines
│   │   ├── auth/              # Authentication service
│   │   ├── database/          # Database connection service
│   │   ├── schema_expansion/  # Schema inference service
│   │   ├── ml/                # NL2SQL model inference
│   │   ├── preprocessing/     # Query preprocessing
│   │   └── ...
│   ├── schemas/               # Pydantic models
│   ├── utils/                 # Utilities
│   └── main.py                # FastAPI app entry point
│
├── frontend/                   # Next.js Frontend
│   ├── app/                   # Next.js App Router
│   ├── components/            # React components
│   ├── lib/                   # API client
│   ├── types/                 # TypeScript types
│   └── package.json
│
├── datamind_t5/               # ML Model & Training
│   ├── final_finetuned/       # Trained T5 model
│   ├── spider/                # Training dataset
│   ├── train.py               # Training script
│   └── infer.py               # Inference script
│
├── tests/                     # Test files
│   ├── test_postgres_schema.py
│   ├── test_nl2sql_postgres.py
│   ├── setup_postgres_test.sql
│   └── README.md
│
├── docs/                      # Documentation
│   ├── architecture.md
│   ├── training.md
│   └── SCHEMA_INFERENCE.md
│
├── logs/                      # Runtime logs (gitignored)
│   ├── backend.log
│   └── frontend.log
│
├── start.sh                   # One-command startup script
├── stop.sh                    # Stop all services
├── requirements.txt           # Python dependencies
├── DEMO_GUIDE.md             # Full demo walkthrough
├── SYSTEM_STATUS.md          # Current system status
└── README.md                 # This file
```

---

## Core Engines

| Engine           | Responsibility                      |
| ---------------- | ----------------------------------- |
| Auth & Session   | User authentication, session state  |
| Database         | DB connection, schema introspection |
| Preprocessing    | Query normalization                 |
| Schema Linking   | Map NL terms → schema candidates    |
| Schema Expansion | Final schema & join selection       |
| ML (Inference)   | Generate SQL from NL                |
| SQL Validation   | Enforce safety & read-only rules    |
| Execution        | Run validated SQL                   |
| Visualization    | Tables & charts                     |

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

## Machine Learning

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

## Running the Application

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

### 4. Quick Start with NL2SQL

The application includes a ready-to-use NL2SQL endpoint that converts natural language questions to SQL:

```bash
# See the quick start guide
cat QUICKSTART_NL2SQL.md

# Test the service
python test_nl2sql.py
```

**Example API Request:**

```bash
curl -X POST "http://localhost:8000/query/nl2sql" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How many users are from USA?",
    "schema": {
      "users": ["id", "name", "email", "country"]
    },
    "use_sanitizer": true
  }'
```

For detailed documentation on the NL2SQL endpoint, see:

- `QUICKSTART_NL2SQL.md` - Quick start guide
- `docs/nl2sql_integration.md` - Full integration documentation
- `NL2SQL_IMPLEMENTATION_SUMMARY.md` - Implementation details

---

## Developer Notes

- Follow `DEVELOPER_GUIDELINES.md` strictly
- Do not introduce cross-engine imports
- Do not add logic to API routes
- Training and inference must remain separate

---

## Academic Context

This project is developed as part of a **B.Tech Computer Science & Engineering Major Project** and demonstrates:

- Applied NLP & Transformers
- Secure database interaction
- Modular backend architecture
- Practical ML system design

---

## Disclaimer

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
