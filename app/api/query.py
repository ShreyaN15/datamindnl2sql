"""
Query API Endpoints
"""

from fastapi import APIRouter, HTTPException, status
from typing import Union
import logging

from app.schemas.query import (
    NL2SQLRequest, 
    NL2SQLResponse, 
    NL2SQLDetailedResponse
)
from app.engines.ml.nl2sql_service import get_nl2sql_service
from app.utils.schema_builder import build_schema_from_dict

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/nl2sql",
    response_model=Union[NL2SQLResponse, NL2SQLDetailedResponse],
    summary="Convert natural language to SQL",
    description="Converts a natural language question to SQL query using fine-tuned T5 model with SQL sanitizer"
)
async def generate_sql(request: NL2SQLRequest):
    """
    Generate SQL from natural language question.
    
    This endpoint uses a fine-tuned T5 model trained on the Spider dataset
    to convert natural language questions into SQL queries. It includes
    an SQL sanitizer that validates and corrects the generated SQL.
    
    **Features:**
    - Schema-agnostic (works with any database schema)
    - SQL validation and correction
    - Foreign key relationship support
    - ~90% accuracy on unseen schemas
    
    **Example:**
    ```python
    {
        "question": "How many users are from USA?",
        "schema": {
            "users": ["id", "name", "email", "country"]
        },
        "use_sanitizer": true,
        "return_details": false
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
            # Return simple response
            sql = nl2sql_service.generate_sql(
                question=request.question,
                schema_text=schema_text,
                foreign_keys=fks,
                use_sanitizer=request.use_sanitizer
            )
            return NL2SQLResponse(
                sql=sql,
                question=request.question
            )
    
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

