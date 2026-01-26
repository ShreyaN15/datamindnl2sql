"""
Query API Endpoints
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.orm import Session
from typing import Union
import logging

from app.schemas.query import (
    NL2SQLRequest, 
    NL2SQLResponse, 
    NL2SQLDetailedResponse,
    QueryExecutionResult
)
from app.engines.ml.nl2sql_service import get_nl2sql_service
from app.engines.execution.service import get_execution_service
from app.utils.schema_builder import build_schema_from_dict
from app.db.session import get_db
from app.db.models import DatabaseConnection, User

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/nl2sql",
    response_model=Union[NL2SQLResponse, NL2SQLDetailedResponse],
    summary="Convert natural language to SQL",
    description="Converts a natural language question to SQL query using fine-tuned T5 model with SQL sanitizer"
)
async def generate_sql(
    request: NL2SQLRequest,
    user_id: int = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """
    Generate SQL from natural language question.
    
    This endpoint uses a fine-tuned T5 model trained on the Spider dataset
    to convert natural language questions into SQL queries. It includes
    an SQL sanitizer that validates and corrects the generated SQL.
    
    **Features:**
    - Schema-agnostic (works with any database schema)
    - SQL validation and correction
    - Foreign key relationship support
    - Optional query execution with results
    - ~90% accuracy on unseen schemas
    
    **Example:**
    ```python
    {
        "question": "How many users are from USA?",
        "schema": {
            "users": ["id", "name", "email", "country"]
        },
        "use_sanitizer": true,
        "return_details": false,
        "execute_query": true,
        "database_id": 1
    }
    ```
    """
    try:
        # Get the NL2SQL service
        nl2sql_service = get_nl2sql_service()
        
        # Convert foreign keys from Pydantic models to tuples
        foreign_keys = None
        if request.foreign_keys:
            foreign_keys = [
                (fk.from_table, fk.from_column, fk.to_table, fk.to_column)
                for fk in request.foreign_keys
            ]
        
        # Build schema text from dictionary
        schema_text, fks = build_schema_from_dict(request.db_schema, foreign_keys)
        
        # Generate SQL
        if request.return_details:
            # Return detailed validation information
            result = nl2sql_service.generate_sql_with_details(
                question=request.question,
                schema_text=schema_text,
                foreign_keys=fks,
                use_sanitizer=request.use_sanitizer
            )
            return NL2SQLDetailedResponse(**result)
        else:
            # Generate SQL
            sql = nl2sql_service.generate_sql(
                question=request.question,
                schema_text=schema_text,
                foreign_keys=fks,
                use_sanitizer=request.use_sanitizer
            )
            
            # Execute query if requested
            execution_result = None
            if request.execute_query:
                if not request.database_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="database_id is required when execute_query is True"
                    )
                
                # Get database connection
                db_conn = db.query(DatabaseConnection).filter(
                    DatabaseConnection.id == request.database_id,
                    DatabaseConnection.user_id == user_id
                ).first()
                
                if not db_conn:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Database connection not found"
                    )
                
                # Execute the query
                execution_service = get_execution_service()
                exec_result = execution_service.execute_query(
                    sql_query=sql,
                    db_type=db_conn.db_type,
                    host=db_conn.host,
                    port=db_conn.port,
                    database=db_conn.database_name,
                    username=db_conn.username,
                    password=db_conn.password
                )
                
                # Analyze query for visualization
                query_type = execution_service.analyze_query_type(sql)
                is_visualizable = False
                suggested_chart = None
                
                if exec_result['success'] and exec_result['data']:
                    is_visualizable, suggested_chart = execution_service.is_visualizable(
                        exec_result['data'],
                        exec_result['columns']
                    )
                
                execution_result = QueryExecutionResult(
                    success=exec_result['success'],
                    data=exec_result['data'],
                    columns=exec_result['columns'],
                    row_count=exec_result['row_count'],
                    has_more=exec_result['has_more'],
                    error=exec_result['error'],
                    query_type=query_type,
                    is_visualizable=is_visualizable,
                    suggested_chart=suggested_chart
                )
            
            return NL2SQLResponse(
                sql=sql,
                question=request.question,
                execution_result=execution_result
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating SQL: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate SQL: {str(e)}"
        )


@router.get("/health", summary="Health check for NL2SQL service")
async def nl2sql_health():
    """Check if the NL2SQL model is loaded and ready"""
    try:
        nl2sql_service = get_nl2sql_service()
        if not nl2sql_service.is_loaded:
            nl2sql_service.load_model()
        return {
            "status": "healthy",
            "model_loaded": nl2sql_service.is_loaded,
            "model_path": str(nl2sql_service.model_path)
        }
    except Exception as e:
        logger.error(f"NL2SQL health check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"NL2SQL service unavailable: {str(e)}"
        )

