# DataMind NL2SQL - Quick Reference

## 🚀 Starting the Application

```bash
./start.sh
```

**What it does:**

- Checks prerequisites (Python, Node.js)
- Kills any processes on ports 8000 & 3000
- Starts backend API on http://localhost:8000
- Starts frontend UI on http://localhost:3000
- Saves process IDs for cleanup
- Displays status and log locations

## 🛑 Stopping the Application

```bash
./stop.sh
```

**What it does:**

- Stops both backend and frontend processes
- Cleans up PID files
- Frees up ports 8000 and 3000

## 📁 Project Structure

```
datamindnl2sql/
├── start.sh              # Start everything
├── stop.sh               # Stop everything
├── app/                  # FastAPI backend
├── frontend/             # Next.js UI
├── tests/                # All test files
├── logs/                 # Runtime logs
└── datamind_t5/          # ML model
```

## 🔍 Viewing Logs

**Backend logs:**

```bash
tail -f logs/backend.log
```

**Frontend logs:**

```bash
tail -f logs/frontend.log
```

**Both:**

```bash
tail -f logs/*.log
```

## 🧪 Running Tests

**Test schema inference:**

```bash
source venv/bin/activate
python tests/test_postgres_schema.py
```

**Test NL2SQL:**

```bash
python tests/test_nl2sql_postgres.py
```

## 🌐 Access Points

| Service     | URL                        | Description |
| ----------- | -------------------------- | ----------- |
| Frontend    | http://localhost:3000      | Main UI     |
| Backend API | http://localhost:8000      | REST API    |
| API Docs    | http://localhost:8000/docs | Swagger UI  |

## 💾 Database Setup

**Create test database:**

```bash
psql -U postgres -d postgres -f tests/setup_postgres_test.sql
```

**Test database details:**

- Name: `datamind_test`
- Tables: 6 (users, products, categories, orders, order_items, reviews)
- Sample data: E-commerce dataset
- Foreign keys: 6 relationships

## 🔑 Demo Credentials

**Create account at:** http://localhost:3000

**Test database connection:**

```
Name: E-Commerce Test
Type: PostgreSQL
Host: localhost
Port: 5432
Database: datamind_test
Username: postgres
Password: [your postgres password]
```

## 📝 Example Queries

**Simple:**

- "Show all users"
- "List all products"
- "Find the most expensive product"

**With JOINs:**

- "Show products with their categories"
- "List orders with user names"
- "Show product reviews with user names"

**Aggregations:**

- "Count orders per user"
- "Find average product price"
- "Total revenue from all orders"

## 🛠️ Manual Commands

**Backend only:**

```bash
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Frontend only:**

```bash
cd frontend
npm run dev
```

**Install dependencies:**

```bash
# Backend
pip install -r requirements.txt

# Frontend
cd frontend && npm install
```

## 📊 System Status Check

**Check if services are running:**

```bash
# Backend
curl http://localhost:8000/health

# Frontend
curl http://localhost:3000

# Or check processes
lsof -i:8000  # Backend
lsof -i:3000  # Frontend
```

## 🐛 Troubleshooting

**Port already in use:**

```bash
./stop.sh  # Kills processes on ports
./start.sh # Restart fresh
```

**Backend won't start:**

```bash
tail -f logs/backend.log  # Check errors
source venv/bin/activate
pip install -r requirements.txt
```

**Frontend won't start:**

```bash
tail -f logs/frontend.log  # Check errors
cd frontend && npm install
```

**Database connection fails:**

```bash
# Verify PostgreSQL is running
psql -U postgres -l

# Test connection manually
psql -U postgres -d datamind_test
```

## 📚 Documentation

- `README.md` - Main project documentation
- `DEMO_GUIDE.md` - Complete demo walkthrough
- `SYSTEM_STATUS.md` - Current system status
- `frontend/README.md` - Frontend specific docs
- `tests/README.md` - Testing documentation
- `docs/SCHEMA_INFERENCE.md` - Schema inference details

## 🎯 Common Workflows

**First time setup:**

```bash
# 1. Install dependencies
pip install -r requirements.txt
cd frontend && npm install

# 2. Setup test database
psql -U postgres -f tests/setup_postgres_test.sql

# 3. Start application
./start.sh
```

**Daily development:**

```bash
# Start everything
./start.sh

# Work on your changes...

# Stop when done
./stop.sh
```

**Testing changes:**

```bash
# Run tests
source venv/bin/activate
python tests/test_postgres_schema.py
python tests/test_nl2sql_postgres.py

# Test in browser
open http://localhost:3000
```

## ✨ Features

✅ Automatic schema inference  
✅ Multi-method FK detection  
✅ NL2SQL with T5 model  
✅ Web UI (React/Next.js)  
✅ Authentication (JWT)  
✅ Multi-database support  
✅ Real-time schema refresh  
✅ One-command startup

---

**Quick Start:** `./start.sh` → Open http://localhost:3000 → Register → Add DB → Query!
