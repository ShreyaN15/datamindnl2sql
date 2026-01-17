"""
Database Connection API Endpoints

Endpoints for managing user database connections
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.schemas.db import (
    DatabaseConnectionCreate,
    DatabaseConnectionUpdate,
    DatabaseConnectionResponse,
    DatabaseTestResponse,
    DatabaseConnectionList
)
from app.db.models import DatabaseConnection, User
from app.db.session import get_db
from app.engines.database.connection_service import DatabaseConnectionService
from app.engines.schema_expansion.schema_inference_service import SchemaInferenceService
import json

logger = logging.getLogger(__name__)

router = APIRouter()
schema_inference_service = SchemaInferenceService()


@router.post(
    "/connections",
    response_model=DatabaseConnectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create database connection",
    description="Create a new database connection configuration"
)
def create_connection(
    user_id: int,
    connection_data: DatabaseConnectionCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new database connection for a user.
    
    - **user_id**: ID of the user creating the connection
    - **name**: User-friendly name for the connection
    - **db_type**: Type of database (mysql, postgresql, sqlite, etc.)
    - **host**, **port**, **database_name**, **username**, **password**: Connection details
    - **connection_string**: Optional custom connection string
    """
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Check if connection name already exists for this user
    existing_conn = db.query(DatabaseConnection).filter(
        DatabaseConnection.user_id == user_id,
        DatabaseConnection.name == connection_data.name
    ).first()
    
    if existing_conn:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Connection with name '{connection_data.name}' already exists for this user"
        )
    
    # Create new connection
    new_connection = DatabaseConnection(
        user_id=user_id,
        name=connection_data.name,
        db_type=connection_data.db_type.value,
        host=connection_data.host,
        port=connection_data.port,
        database_name=connection_data.database_name,
        username=connection_data.username,
        password=connection_data.password,  # In production, encrypt this!
        connection_string=connection_data.connection_string,
        is_active=True,
        last_test_status="not_tested"
    )
    
    db.add(new_connection)
    db.commit()
    db.refresh(new_connection)
    
    # AUTO-INFER SCHEMA: Extract schema information from the database
    try:
        logger.info(f"Auto-inferring schema for connection: {new_connection.name}")
        
        # Build connection string
        conn_string = DatabaseConnectionService.build_connection_string(
            db_type=new_connection.db_type,
            host=new_connection.host,
            port=new_connection.port,
            database_name=new_connection.database_name,
            username=new_connection.username,
            password=new_connection.password,
            custom_string=new_connection.connection_string
        )
        
        # Determine connect_args based on db_type
        if new_connection.db_type.lower() == 'sqlite':
            connect_args = {"check_same_thread": False}
        else:
            connect_args = {"connect_timeout": 10}
        
        # Infer schema from the actual database
        schema_data = schema_inference_service.infer_schema_from_connection(
            connection_string=conn_string,
            db_type=new_connection.db_type,
            connect_args=connect_args
        )
        
        # Store schema information in the connection
        new_connection.schema_text = schema_data['schema_text']
        new_connection.schema_tables = json.dumps(schema_data['tables'])
        new_connection.foreign_keys = json.dumps([list(fk) for fk in schema_data['foreign_keys']])
        new_connection.primary_keys = json.dumps(schema_data['primary_keys'])
        new_connection.column_types = json.dumps({f"{k[0]}.{k[1]}": v for k, v in schema_data['column_types'].items()})
        new_connection.table_count = schema_data['table_count']
        new_connection.total_columns = schema_data['total_columns']
        new_connection.schema_extracted_at = datetime.utcnow()
        
        db.commit()
        db.refresh(new_connection)
        
        logger.info(f"Schema extracted: {schema_data['table_count']} tables, {schema_data['total_columns']} columns, {len(schema_data['foreign_keys'])} foreign keys")
        
    except Exception as e:
        logger.warning(f"Schema inference failed for connection {new_connection.name}: {e}")
        # Don't fail the connection creation if schema inference fails
        # User can still use the connection, just without auto-inferred schema
    
    logger.info(f"Database connection created: {new_connection.name} (ID: {new_connection.id}) for user {user_id}")
    
    return new_connection


@router.get(
    "/connections",
    response_model=DatabaseConnectionList,
    summary="List database connections",
    description="Get all database connections for a user"
)
def list_connections(
    user_id: int = Query(..., description="User ID to filter connections"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """List all database connections for a user"""
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    connections = db.query(DatabaseConnection).filter(
        DatabaseConnection.user_id == user_id
    ).offset(skip).limit(limit).all()
    
    total = db.query(DatabaseConnection).filter(
        DatabaseConnection.user_id == user_id
    ).count()
    
    return DatabaseConnectionList(connections=connections, total=total)


@router.get(
    "/connections/{connection_id}",
    response_model=DatabaseConnectionResponse,
    summary="Get database connection",
    description="Get details of a specific database connection"
)
def get_connection(
    connection_id: int,
    user_id: int = Query(..., description="User ID for authorization"),
    db: Session = Depends(get_db)
):
    """Get a specific database connection"""
    connection = db.query(DatabaseConnection).filter(
        DatabaseConnection.id == connection_id,
        DatabaseConnection.user_id == user_id
    ).first()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connection with ID {connection_id} not found for user {user_id}"
        )
    
    return connection


@router.put(
    "/connections/{connection_id}",
    response_model=DatabaseConnectionResponse,
    summary="Update database connection",
    description="Update an existing database connection"
)
def update_connection(
    connection_id: int,
    user_id: int,
    connection_update: DatabaseConnectionUpdate,
    db: Session = Depends(get_db)
):
    """Update a database connection"""
    connection = db.query(DatabaseConnection).filter(
        DatabaseConnection.id == connection_id,
        DatabaseConnection.user_id == user_id
    ).first()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connection with ID {connection_id} not found for user {user_id}"
        )
    
    # Update fields if provided
    update_data = connection_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(connection, field, value)
    
    # Reset test status if connection details changed
    if any(k in update_data for k in ['host', 'port', 'database_name', 'username', 'password', 'connection_string']):
        connection.last_test_status = "not_tested"
        connection.last_tested_at = None
    
    db.commit()
    db.refresh(connection)
    
    logger.info(f"Database connection updated: {connection.name} (ID: {connection.id})")
    
    return connection


@router.delete(
    "/connections/{connection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete database connection",
    description="Delete a database connection"
)
def delete_connection(
    connection_id: int,
    user_id: int = Query(..., description="User ID for authorization"),
    db: Session = Depends(get_db)
):
    """Delete a database connection"""
    connection = db.query(DatabaseConnection).filter(
        DatabaseConnection.id == connection_id,
        DatabaseConnection.user_id == user_id
    ).first()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connection with ID {connection_id} not found for user {user_id}"
        )
    
    db.delete(connection)
    db.commit()
    
    logger.info(f"Database connection deleted: {connection.name} (ID: {connection.id})")
    
    return None


@router.post(
    "/connections/{connection_id}/test",
    response_model=DatabaseTestResponse,
    summary="Test database connection",
    description="Test if a database connection is working"
)
def test_connection(
    connection_id: int,
    user_id: int = Query(..., description="User ID for authorization"),
    db: Session = Depends(get_db)
):
    """Test a database connection"""
    connection = db.query(DatabaseConnection).filter(
        DatabaseConnection.id == connection_id,
        DatabaseConnection.user_id == user_id
    ).first()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connection with ID {connection_id} not found for user {user_id}"
        )
    
    # Build connection string
    try:
        conn_string = DatabaseConnectionService.build_connection_string(
            db_type=connection.db_type,
            host=connection.host,
            port=connection.port,
            database_name=connection.database_name,
            username=connection.username,
            password=connection.password,
            custom_string=connection.connection_string
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Test the connection
    success, message, details = DatabaseConnectionService.test_connection(conn_string)
    
    # Update connection with test results
    connection.last_tested_at = datetime.utcnow()
    connection.last_test_status = "success" if success else "failed"
    db.commit()
    
    logger.info(f"Database connection tested: {connection.name} (ID: {connection.id}) - Status: {connection.last_test_status}")
    
    return DatabaseTestResponse(
        connection_id=connection.id,
        status="success" if success else "failed",
        message=message,
        tested_at=connection.last_tested_at,
        details=details
    )


@router.get(
    "/connections/{connection_id}/schema",
    summary="Get database schema",
    description="Retrieve schema information (tables and columns) from a database connection"
)
def get_connection_schema(
    connection_id: int,
    user_id: int = Query(..., description="User ID for authorization"),
    use_cached: bool = Query(True, description="Use cached schema if available"),
    db: Session = Depends(get_db)
):
    """
    Get schema information from a database connection.
    
    - If use_cached=True and schema was previously extracted, returns cached schema
    - If use_cached=False or no cached schema exists, extracts fresh schema from database
    """
    connection = db.query(DatabaseConnection).filter(
        DatabaseConnection.id == connection_id,
        DatabaseConnection.user_id == user_id
    ).first()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connection with ID {connection_id} not found for user {user_id}"
        )
    
    # Check if we have cached schema and user wants to use it
    if use_cached and connection.schema_text:
        logger.info(f"Returning cached schema for connection {connection.name}")
        
        # Parse stored schema data
        tables = json.loads(connection.schema_tables) if connection.schema_tables else {}
        foreign_keys = json.loads(connection.foreign_keys) if connection.foreign_keys else []
        primary_keys = json.loads(connection.primary_keys) if connection.primary_keys else {}
        
        return {
            "connection_id": connection.id,
            "connection_name": connection.name,
            "database_name": connection.database_name,
            "db_type": connection.db_type,
            "schema_text": connection.schema_text,
            "tables": tables,
            "foreign_keys": foreign_keys,
            "primary_keys": primary_keys,
            "table_count": connection.table_count,
            "total_columns": connection.total_columns,
            "schema_extracted_at": connection.schema_extracted_at,
            "cached": True
        }
    
    # Extract fresh schema from database
    logger.info(f"Extracting fresh schema for connection {connection.name}")
    
    # Build connection string
    try:
        conn_string = DatabaseConnectionService.build_connection_string(
            db_type=connection.db_type,
            host=connection.host,
            port=connection.port,
            database_name=connection.database_name,
            username=connection.username,
            password=connection.password,
            custom_string=connection.connection_string
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Determine connect_args
    if connection.db_type.lower() == 'sqlite':
        connect_args = {"check_same_thread": False}
    else:
        connect_args = {"connect_timeout": 10}
    
    # Infer schema
    try:
        schema_data = schema_inference_service.infer_schema_from_connection(
            connection_string=conn_string,
            db_type=connection.db_type,
            connect_args=connect_args
        )
        
        # Update cached schema in database
        connection.schema_text = schema_data['schema_text']
        connection.schema_tables = json.dumps(schema_data['tables'])
        connection.foreign_keys = json.dumps([list(fk) for fk in schema_data['foreign_keys']])
        connection.primary_keys = json.dumps(schema_data['primary_keys'])
        connection.column_types = json.dumps({f"{k[0]}.{k[1]}": v for k, v in schema_data['column_types'].items()})
        connection.table_count = schema_data['table_count']
        connection.total_columns = schema_data['total_columns']
        connection.schema_extracted_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "connection_id": connection.id,
            "connection_name": connection.name,
            "database_name": connection.database_name,
            "db_type": connection.db_type,
            "schema_text": schema_data['schema_text'],
            "tables": schema_data['tables'],
            "foreign_keys": schema_data['foreign_keys'],
            "primary_keys": schema_data['primary_keys'],
            "table_count": schema_data['table_count'],
            "total_columns": schema_data['total_columns'],
            "schema_extracted_at": connection.schema_extracted_at,
            "cached": False
        }
        
    except Exception as e:
        logger.error(f"Schema extraction failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract schema: {str(e)}"
        )


@router.post(
    "/connections/{connection_id}/refresh-schema",
    summary="Refresh database schema",
    description="Re-extract and update schema information from the database"
)
def refresh_connection_schema(
    connection_id: int,
    user_id: int = Query(..., description="User ID for authorization"),
    db: Session = Depends(get_db)
):
    """
    Force re-extraction of schema from the database.
    
    Useful when the database structure has changed.
    """
    # Just call get_connection_schema with use_cached=False
    return get_connection_schema(
        connection_id=connection_id,
        user_id=user_id,
        use_cached=False,
        db=db
    )

