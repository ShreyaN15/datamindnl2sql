# NL2SQL Integration Guide

This directory contains the integrated NL2SQL (Natural Language to SQL) system for the DataMind API.

## 📁 Structure

```
app/
├── engines/
│   ├── ml/
│   │   ├── nl2sql_service.py      # Main NL2SQL inference service
│   │   └── ...
│   └── sql_validation/
│       └── validator.py            # SQL sanitizer/validator
├── utils/
│   └── schema_builder.py           # Schema utilities
├── schemas/
│   └── query.py                    # Pydantic schemas for API
└── api/
    └── query.py                    # NL2SQL API endpoints

models/
└── nl2sql-t5/                      # Fine-tuned T5 model (~900MB)
```

## 🎯 Features

- **Fine-tuned T5 Model**: Trained on Spider dataset (23 epochs, 7K samples)
- **SQL Sanitizer**: Validates and corrects generated SQL
- **Schema-Agnostic**: Works with any database schema
- **~90% Accuracy**: On unseen schemas across diverse domains

## 🚀 API Usage

### Endpoint: `/query/nl2sql`

**Basic Request:**

```json
POST /query/nl2sql
{
  "question": "How many users are from USA?",
  "schema": {
    "users": ["id", "name", "email", "country"]
  },
  "use_sanitizer": true,
  "return_details": false
}
```

**Response:**

```json
{
  "sql": "SELECT COUNT(*) FROM users WHERE country = 'USA'",
  "question": "How many users are from USA?"
}
```

**With Foreign Keys:**

```json
{
  "question": "Show users who have placed orders",
  "schema": {
    "users": ["id", "name", "email"],
    "orders": ["id", "user_id", "total"]
  },
  "foreign_keys": [
    {
      "from_table": "orders",
      "from_column": "user_id",
      "to_table": "users",
      "to_column": "id"
    }
  ],
  "use_sanitizer": true
}
```

**Detailed Response (with validation info):**

```json
{
  "question": "How many users are from USA?",
  "return_details": true,
  "schema": { ... },
  "use_sanitizer": true
}
```

Returns:

```json
{
  "question": "How many users are from USA?",
  "raw_sql": "SELECT COUNT(*) FROM users WHERE Country = 'USA'",
  "corrected_sql": "SELECT COUNT(*) FROM users WHERE country = 'USA'",
  "is_valid": true,
  "errors": ["Fixed column case: 'Country' -> 'country'"],
  "was_corrected": true
}
```

## 🔧 Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:

- `torch>=2.0.0`
- `transformers>=4.30.0`
- `sentencepiece>=0.1.99`
- `sqlparse>=0.4.4`
- `sqlglot>=20.0.0`

### 2. Verify Model Location

The model should be at: `models/nl2sql-t5/`

### 3. Test the Service

```bash
python test_nl2sql.py
```

### 4. Run the API

```bash
uvicorn app.main:app --reload
```

Then visit: `http://localhost:8000/docs` for interactive API documentation.

## 📝 How It Works

### 1. Schema Input

You provide the database schema as a dictionary:

```python
schema = {
    "table_name": ["column1", "column2", ...],
    ...
}
```

### 2. SQL Generation

The fine-tuned T5 model generates SQL from your natural language question.

### 3. SQL Sanitizer (Optional)

The sanitizer:

- ✅ Validates column and table names against schema
- ✅ Fixes case mismatches (e.g., `Country` → `country`)
- ✅ Auto-qualifies columns when needed (e.g., `name` → `users.name`)
- ✅ Validates JOIN conditions against foreign keys
- ✅ Detects and reports errors

### 4. Response

You get a valid, corrected SQL query ready to execute.

## 🧪 Testing Examples

### Example 1: Simple Query

```python
from app.engines.ml.nl2sql_service import get_nl2sql_service

service = get_nl2sql_service()
service.load_model()

sql = service.generate_from_dict(
    question="How many users are active?",
    tables_dict={"users": ["id", "name", "is_active"]},
    use_sanitizer=True
)
# Result: SELECT COUNT(*) FROM users WHERE is_active = 1
```

### Example 2: Join Query

```python
sql = service.generate_from_dict(
    question="List all orders with customer names",
    tables_dict={
        "customers": ["id", "name"],
        "orders": ["id", "customer_id", "total"]
    },
    foreign_keys=[("orders", "customer_id", "customers", "id")],
    use_sanitizer=True
)
# Result: SELECT orders.id, customers.name, orders.total
#         FROM orders JOIN customers ON orders.customer_id = customers.id
```

## 🔍 Health Check

Check if the service is ready:

```bash
GET /query/health
```

Response:

```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_path": "models/nl2sql-t5"
}
```

## ⚙️ Configuration

### Enable/Disable Sanitizer

Set `use_sanitizer: false` to get raw model output without validation.

### Detailed Validation Info

Set `return_details: true` to get validation errors and corrections.

## 🎓 Model Information

- **Base Model**: T5-base (220M parameters)
- **Training Dataset**: Spider (7K SQL examples)
- **Training**: 23 epochs
- **Accuracy**: ~90% on unseen schemas
- **Model Size**: ~900MB

## 📚 Related Files

- **Original Implementation**: `datamind_t5/infer.py`
- **Integration Guide**: `datamind_t5/INTEGRATION_GUIDE.md`
- **Training Scripts**: `datamind_t5/train.py` (reference only)

## 🛠️ Development Notes

The implementation follows the repository's conventions:

- ✅ Services in `app/engines/`
- ✅ Utilities in `app/utils/`
- ✅ Schemas in `app/schemas/`
- ✅ API routes in `app/api/`
- ✅ Models in `models/`

All logic is self-contained and doesn't reference the `datamind_t5/` directory.

## 🐛 Troubleshooting

### Model Not Found

Ensure `models/nl2sql-t5/` exists and contains:

- `model.safetensors`
- `config.json`
- `tokenizer_config.json`
- `spiece.model`

### Out of Memory

The model requires ~2GB RAM. For production, consider:

- Using GPU if available
- Implementing model caching
- Using quantized models

### Slow First Request

The model loads lazily on first request. Implement eager loading in production:

```python
@app.on_event("startup")
async def startup_event():
    from app.engines.ml.nl2sql_service import get_nl2sql_service
    service = get_nl2sql_service()
    service.load_model()
```

## 📄 License

This implementation uses the fine-tuned T5 model trained on the Spider dataset.
