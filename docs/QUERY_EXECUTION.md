# Query Execution & Visualization Feature

## Overview

Added complete query execution and visualization capabilities to the DataMind NL2SQL system.

## ✨ New Features

### 1. **SQL Query Execution**
- Execute generated SQL queries directly against connected databases
- Support for PostgreSQL, MySQL, and SQLite
- Graceful error handling with detailed error messages
- Results limited to 1000 rows for performance
- Query timeout protection (30 seconds)

### 2. **Results Display**
- Tabular display of query results
- Scrollable table with sticky headers
- Clean formatting with null value handling
- Row count display
- Visual success/error indicators

### 3. **Data Visualization**
- Automatic detection of visualizable data
- Bar chart visualization for categorical data
- Support for aggregation queries
- Visual chart type suggestions
- Gradient backgrounds for better aesthetics

### 4. **Error Handling**
- SQL generation errors are caught and displayed
- Execution errors show detailed error messages
- Fallback behavior: SQL is still shown even if execution fails
- User-friendly error explanations

## 🔧 Implementation Details

### Backend Changes

**New Files:**
- `app/engines/execution/service.py` - Query execution engine with safety features

**Updated Files:**
- `app/api/query.py` - Added execution support to NL2SQL endpoint
- `app/schemas/query.py` - Added execution result schemas

**Key Features:**
```python
class QueryExecutionService:
    - execute_query() - Execute SQL with timeout and row limits
    - analyze_query_type() - Detect query type (SELECT, INSERT, etc.)
    - is_visualizable() - Determine if results can be visualized
    - Automatic chart type suggestion (bar, line, histogram)
```

### Frontend Changes

**Updated Files:**
- `frontend/types/api.ts` - Added QueryExecutionResult interface
- `frontend/components/NL2SQLQuery.tsx` - Complete UI overhaul

**UI Components:**
1. **Execution Toggle**
   - Checkbox to enable/disable query execution
   - Dynamic button text based on toggle state

2. **Results Table**
   - Responsive table with overflow handling
   - Sticky headers for scrolling
   - Hover effects on rows
   - Clean column/row formatting

3. **Visualization**
   - Bar chart with percentage-based widths
   - Color-coded bars (indigo)
   - Labels and values displayed
   - Limited to top 10 results for clarity

4. **Status Indicators**
   - Green success badge with checkmark
   - Red error badge with X icon
   - Row count display
   - "Has more" indicator for limited results

## 📊 Supported Visualizations

### Bar Chart
**When:** 2 columns (1 categorical, 1 numeric)
**Example Query:** "Count orders per user"
```
User A: ████████████████ 15
User B: ██████████ 10
User C: ████████ 8
```

### Line Chart (Placeholder)
**When:** Multiple numeric columns
**Note:** Currently shows placeholder, full implementation coming soon

### Other Charts
**When:** Complex data patterns detected
**Note:** Shows placeholder with chart type suggestion

## 🔒 Safety Features

### Query Execution Limits
- **Row Limit:** Maximum 1000 rows returned
- **Timeout:** 30 seconds max execution time
- **Read-Only:** Only SELECT queries recommended
- **Connection Pooling:** Automatic cleanup after execution

### Error Handling
```python
try:
    # Execute query
    result = execute_query(sql, db_params)
except SQLAlchemyError as e:
    # Graceful fallback
    return {
        'success': False,
        'error': str(e),
        'data': []
    }
```

## 🎯 Usage Guide

### Via UI (Recommended)

1. **Login** to http://localhost:3000
2. **Add Database Connection**
   - Use your PostgreSQL database
   - Test connection to verify

3. **Go to Query Tab**
4. **Select Database**
5. **Check "Execute query and show results"**
6. **Ask Question**
   - "Show all users"
   - "List top 5 expensive products"
   - "Count orders per customer"

7. **View Results**
   - SQL query (always shown)
   - Execution results (table)
   - Visualization (if applicable)

### Via API

```bash
curl -X POST http://localhost:8000/query/nl2sql \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Show all users",
    "schema": {"users": ["id", "username", "email"]},
    "execute_query": true,
    "database_id": 1
  }'
```

**Response:**
```json
{
  "sql": "SELECT * FROM users",
  "question": "Show all users",
  "execution_result": {
    "success": true,
    "data": [
      {"id": 1, "username": "alice", "email": "alice@example.com"},
      {"id": 2, "username": "bob", "email": "bob@example.com"}
    ],
    "columns": ["id", "username", "email"],
    "row_count": 2,
    "has_more": false,
    "error": null,
    "query_type": "select",
    "is_visualizable": false,
    "suggested_chart": null
  }
}
```

## 🧪 Testing

### Test Queries

**Simple SELECT:**
```sql
Question: "Show all users"
Expected: SELECT * FROM users
Visualizable: No
```

**Aggregation:**
```sql
Question: "Count orders per user"
Expected: SELECT user_id, COUNT(*) FROM orders GROUP BY user_id
Visualizable: Yes (Bar Chart)
```

**TOP N:**
```sql
Question: "Top 5 expensive products"
Expected: SELECT * FROM products ORDER BY price DESC LIMIT 5
Visualizable: Maybe (depends on columns)
```

### Test Script

```bash
cd tests
python test_query_execution.py
```

## 🎨 UI/UX Features

### Visual Indicators
- ✅ Green success badge
- ❌ Red error badge
- 📊 Chart icon for visualizations
- 🔄 Loading spinners
- 📋 Copy SQL button

### Responsive Design
- Scrollable tables
- Responsive grid layouts
- Mobile-friendly sizing
- Overflow handling

### User Feedback
- Clear error messages
- Row count display
- "Has more" indicators
- Loading states

## 📝 Example Workflows

### Workflow 1: Explore Data
1. Connect to database
2. Ask "Show all tables" → See schema
3. Ask "Show first 10 users" → See data
4. Ask "Count users by country" → See visualization

### Workflow 2: Data Analysis
1. Connect to analytics database
2. Ask "Total revenue by month"
3. View bar chart of results
4. Copy SQL for reporting tool
5. Ask "Top 10 customers by revenue"

### Workflow 3: Error Recovery
1. Ask complex question
2. SQL generates correctly
3. Execution fails (syntax error)
4. See error message
5. Still have SQL to debug
6. Refine question and retry

## 🔄 What Changed

### Before
- SQL generation only
- No execution capability
- No result display
- No visualization

### After
- ✅ SQL generation (unchanged)
- ✅ Optional query execution
- ✅ Tabular results display
- ✅ Automatic visualization
- ✅ Error handling with fallback
- ✅ Visual status indicators

## 🚀 Future Enhancements

### Short Term
- [ ] Line chart implementation
- [ ] Pie chart support
- [ ] Export results to CSV/JSON
- [ ] Query history

### Long Term
- [ ] Advanced chart library (Chart.js, Recharts)
- [ ] Interactive visualizations
- [ ] Query optimization suggestions
- [ ] Execution plan display
- [ ] Multi-query batching

## 🔐 Security Notes

- Execution is **opt-in** (checkbox must be checked)
- Requires valid database connection
- User authentication required
- Database credentials never exposed to client
- Query timeout prevents long-running queries
- Row limit prevents memory issues

## 📦 Dependencies

**Backend:**
- `sqlalchemy` - Database connections
- `psycopg2-binary` - PostgreSQL driver
- `pymysql` - MySQL driver

**Frontend:**
- No new dependencies added
- Pure React/TypeScript implementation

## ✅ Testing Checklist

- [x] Backend execution service created
- [x] API endpoint updated
- [x] Frontend types updated
- [x] UI components implemented
- [x] Bar chart visualization working
- [x] Error handling implemented
- [x] Services restarted successfully
- [x] Documentation created

## 🎉 Summary

The query execution and visualization feature is **fully implemented and ready to use**!

**Access:** http://localhost:3000
- Login/Register
- Add database connection
- Navigate to Query tab
- Check "Execute query and show results"
- Start asking questions!

**Key Benefits:**
- See actual data, not just SQL
- Verify query correctness immediately
- Visual insights with charts
- Graceful error handling
- No breaking changes to existing functionality
