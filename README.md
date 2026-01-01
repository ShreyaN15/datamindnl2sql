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
