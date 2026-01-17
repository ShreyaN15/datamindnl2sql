# NL2SQL Integration - Quick Start Guide

## 🚀 Getting Started

### Step 1: Install Dependencies

First, ensure you have Python 3.8+ installed, then install the required packages:

```bash
pip install -r requirements.txt
```

This will install:

- PyTorch (for model inference)
- Transformers (Hugging Face)
- SentencePiece (tokenizer)
- SQLparse & SQLglot (SQL parsing)
- FastAPI & Uvicorn (API framework)
- And other dependencies

**Note**: Installing PyTorch may take some time depending on your system.

### Step 2: Verify Model Files

Ensure the model is properly copied:

```bash
ls -la models/nl2sql-t5/
```

You should see:

- `model.safetensors` (~900MB)
- `config.json`
- `tokenizer_config.json`
- `spiece.model`
- And other config files

### Step 3: Test the Service (Optional)

Run the test script to verify everything works:

```bash
python test_nl2sql.py
```

This will:

1. Load the T5 model
2. Test basic SQL generation
3. Test with validation details
4. Compare with/without sanitizer

**Expected Output**:

```
🚀 Starting NL2SQL Service Tests

================================================================================
TEST 1: Basic SQL Generation
================================================================================

Question: How many users are from USA?
SQL: SELECT COUNT(*) FROM users WHERE country = 'USA'

...

✅ All tests completed successfully!
```

### Step 4: Run the API

Start the FastAPI server:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:

- **API Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **NL2SQL Health**: http://localhost:8000/query/health

### Step 5: Test the API

#### Using the Interactive Docs (Recommended)

1. Go to http://localhost:8000/docs
2. Find the `/query/nl2sql` endpoint
3. Click "Try it out"
4. Use the example request or create your own
5. Click "Execute"

#### Using cURL

```bash
curl -X POST "http://localhost:8000/query/nl2sql" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How many users are from USA?",
    "schema": {
      "users": ["id", "name", "email", "country"]
    },
    "use_sanitizer": true,
    "return_details": false
  }'
```

#### Using Python

```python
import requests

response = requests.post("http://localhost:8000/query/nl2sql", json={
    "question": "How many users are from USA?",
    "schema": {
        "users": ["id", "name", "email", "country"]
    },
    "use_sanitizer": True,
    "return_details": False
})

print(response.json())
# Output: {"sql": "SELECT COUNT(*) FROM users WHERE country = 'USA'", ...}
```

## 🎯 Example Requests

### Example 1: Simple Count Query

```json
{
  "question": "How many customers are active?",
  "schema": {
    "customers": ["id", "name", "email", "is_active"]
  },
  "use_sanitizer": true
}
```

### Example 2: Join Query with Foreign Keys

```json
{
  "question": "List all orders with customer names",
  "schema": {
    "customers": ["id", "name", "email"],
    "orders": ["id", "customer_id", "total", "created_at"]
  },
  "foreign_keys": [
    {
      "from_table": "orders",
      "from_column": "customer_id",
      "to_table": "customers",
      "to_column": "id"
    }
  ],
  "use_sanitizer": true
}
```

### Example 3: Get Validation Details

```json
{
  "question": "What is the average order total?",
  "schema": {
    "orders": ["id", "customer_id", "total", "created_at"]
  },
  "use_sanitizer": true,
  "return_details": true
}
```

## ⚡ Performance Tips

### Enable Eager Loading (Production)

To load the model at startup instead of on first request, add to `app/main.py`:

```python
@app.on_event("startup")
async def startup_event():
    from app.engines.ml.nl2sql_service import get_nl2sql_service
    service = get_nl2sql_service()
    service.load_model()
    logger.info("NL2SQL model loaded at startup")
```

### Use GPU (if available)

The model will automatically use GPU if CUDA is available. To force CPU:

```python
# In nl2sql_service.py, modify load_model():
self.model = T5ForConditionalGeneration.from_pretrained(str(self.model_path))
self.model.to('cpu')  # Force CPU
```

## 🐛 Troubleshooting

### Issue: Model Not Found

**Solution**: Ensure the model is at `models/nl2sql-t5/` (not `models/final_finetuned/`)

### Issue: Import Errors

**Solution**: Install all dependencies: `pip install -r requirements.txt`

### Issue: Out of Memory

**Solution**:

- Close other applications
- Use CPU instead of GPU for inference
- Reduce `num_beams` parameter (lower quality but faster)

### Issue: Slow First Request

**Solution**: Enable eager loading at startup (see Performance Tips above)

### Issue: "Module 'torch' not found"

**Solution**: Install PyTorch:

```bash
pip install torch transformers sentencepiece
```

## 📊 Expected Performance

- **First Request**: 5-10 seconds (model loading)
- **Subsequent Requests**: 0.5-2 seconds (depending on query complexity)
- **Memory Usage**: ~2GB RAM
- **Accuracy**: ~90% on unseen schemas

## 📚 Next Steps

1. Read the full integration guide: `docs/nl2sql_integration.md`
2. Explore the API docs: http://localhost:8000/docs
3. Customize the service for your needs
4. Integrate with your database connection logic
5. Add authentication and rate limiting for production

## ✅ Checklist

- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Model files copied to `models/nl2sql-t5/`
- [ ] Test script runs successfully
- [ ] API server starts without errors
- [ ] Can access API docs at http://localhost:8000/docs
- [ ] Test endpoint returns valid SQL
- [ ] Health check endpoint responds

## 🎓 Learning Resources

- **Original Integration Guide**: `datamind_t5/INTEGRATION_GUIDE.md`
- **API Documentation**: http://localhost:8000/docs (when running)
- **Test Examples**: `test_nl2sql.py`

Happy querying! 🚀
