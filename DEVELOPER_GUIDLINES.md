# Developer Guidelines — DataMind
- authored by Hari 

**Read this before writing code.**  
This project follows a strict modular architecture.  
Breaking these rules will cause rework.

---

## 1. High-Level Architecture (Non-Negotiable)

- ✅ Single FastAPI app
- ✅ Single monorepo
- ✅ Multiple internal engines
- ❌ No microservices
- ❌ No engine-to-engine calls
- **FastAPI is the orchestrator — not a logic layer.**

---

## 2. Folder Responsibility Rules

### `/app/api/`

Contains HTTP routes only:

- ❌ No business logic
- ❌ No DB calls
- ❌ No ML calls
- ✅ Only calls engines in order

### `/app/engines/`

Each engine:

- Owns one responsibility
- Is pure Python
- ❌ Must NOT import FastAPI
- ❌ Must NOT import other engines
- ✅ Can be unit-tested independently

**Rule:** If an engine needs something, it must be passed as a parameter.

### `/training/`

- Offline only
- Used for model training
- ❌ Never imported by FastAPI
- ❌ Never run in production

### `/models/`

- Contains frozen ML artifacts
- Used only for inference
- ❌ No training code here

---

## 3. Engine Ownership Summary

| Engine | Responsibility |
|--------|----------------|
| `auth` | Users, sessions |
| `database` | DB connection, schema, execution |
| `preprocessing` | Text normalization |
| `schema_linking` | NL → schema candidates |
| `schema_expansion` | Final schema + joins |
| `ml` | SQL generation only |
| `sql_validation` | Safety & sanitization |
| `execution` | Run SQL |
| `visualization` | Tables & charts |

> **If logic doesn't clearly belong → ask before coding.**

---

## 4. Import Rules (Very Important)

### ✅ Allowed:

```
api → engines
api → schemas
engines → utils
```

### ❌ Forbidden:

```
engine → engine
engine → api
training → app
app → training
```

**If you need something across engines → pass it explicitly.**

---

## 5. FastAPI Startup Rules

- Models are loaded **once at startup**
- DB connections are created **per session**
- No global mutable state except cache/config

---

## 6. ML-Specific Rules

- ML engine only does **inference**
- ❌ No SQL validation inside ML
- ❌ No DB access inside ML
- Prompt format must remain **fixed**
- If you change the prompt → **document it**

---

## 7. Database Rules

- **Read-only queries only**
- ❌ No schema modification
- ❌ No data storage from user DB
- Only metadata (tables, columns, FKs) may be cached

---

## 8. Coding Standards

- Small functions
- Explicit inputs & outputs
- No magic globals
- Type hints preferred
- **Logs > prints**

---

## 9. Copilot / AI Tooling Rule

Copilot is allowed **only if**:

- Code stays inside assigned folder
- No architectural shortcuts
- No cross-engine imports

**You are responsible for what you commit.**

---

## 10. When in Doubt

Ask before coding, not after.

> _"Is this engine the right place for this logic?"_

---

## Final Reminder

**Architecture > speed.**  
Clean structure matters more than clever code.
