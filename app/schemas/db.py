"""
Database Connection Schemas

Pydantic models for database connection management
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class DatabaseType(str, Enum):
    """Supported database types"""
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"
    MSSQL = "mssql"
    ORACLE = "oracle"


class DatabaseConnectionCreate(BaseModel):
    """Schema for creating a new database connection"""
    name: str = Field(..., min_length=1, max_length=100, description="User-friendly name for the connection")
    db_type: DatabaseType = Field(..., description="Type of database")
    host: Optional[str] = Field(None, max_length=255, description="Database host address")
    port: Optional[int] = Field(None, gt=0, lt=65536, description="Database port")
    database_name: str = Field(..., min_length=1, max_length=100, description="Database name")
    username: Optional[str] = Field(None, max_length=100, description="Database username")
    password: Optional[str] = Field(None, description="Database password")
    connection_string: Optional[str] = Field(None, description="Custom connection string (overrides other fields)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Production MySQL DB",
                "db_type": "mysql",
                "host": "localhost",
                "port": 3306,
                "database_name": "my_database",
                "username": "db_user",
                "password": "db_password"
            }
        }


class DatabaseConnectionUpdate(BaseModel):
    """Schema for updating a database connection"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    host: Optional[str] = Field(None, max_length=255)
    port: Optional[int] = Field(None, gt=0, lt=65536)
    database_name: Optional[str] = Field(None, min_length=1, max_length=100)
    username: Optional[str] = Field(None, max_length=100)
    password: Optional[str] = None
    connection_string: Optional[str] = None
    is_active: Optional[bool] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Updated DB Name",
                "host": "new-host.example.com",
                "is_active": True
            }
        }


class DatabaseConnectionResponse(BaseModel):
    """Schema for database connection in responses (without sensitive data)"""
    id: int
    user_id: int
    name: str
    db_type: str
    host: Optional[str] = None
    port: Optional[int] = None
    database_name: str
    username: Optional[str] = None
    is_active: bool
    last_tested_at: Optional[datetime] = None
    last_test_status: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "user_id": 1,
                "name": "Production MySQL DB",
                "db_type": "mysql",
                "host": "localhost",
                "port": 3306,
                "database_name": "my_database",
                "username": "db_user",
                "is_active": True,
                "last_tested_at": "2026-01-17T10:30:00",
                "last_test_status": "success",
                "created_at": "2026-01-17T10:00:00",
                "updated_at": None
            }
        }


class DatabaseTestRequest(BaseModel):
    """Schema for testing a database connection"""
    connection_id: int = Field(..., description="ID of the database connection to test")
    
    class Config:
        json_schema_extra = {
            "example": {
                "connection_id": 1
            }
        }


class DatabaseTestResponse(BaseModel):
    """Response from database connection test"""
    connection_id: int
    status: str = Field(..., description="success or failed")
    message: str
    tested_at: datetime
    details: Optional[dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "connection_id": 1,
                "status": "success",
                "message": "Connection successful",
                "tested_at": "2026-01-17T10:30:00",
                "details": {
                    "database_version": "MySQL 8.0.32",
                    "tables_count": 15
                }
            }
        }


class DatabaseConnectionList(BaseModel):
    """List of database connections"""
    connections: list[DatabaseConnectionResponse]
    total: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "connections": [
                    {
                        "id": 1,
                        "user_id": 1,
                        "name": "Production DB",
                        "db_type": "mysql",
                        "host": "localhost",
                        "port": 3306,
                        "database_name": "prod_db",
                        "username": "admin",
                        "is_active": True,
                        "last_test_status": "success",
                        "created_at": "2026-01-17T10:00:00"
                    }
                ],
                "total": 1
            }
        }
