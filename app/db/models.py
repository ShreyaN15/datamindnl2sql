"""
Database Models

SQLAlchemy models for User and DatabaseConnection
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class User(Base):
    """User model for authentication and user management"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    database_connections = relationship("DatabaseConnection", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


class DatabaseConnection(Base):
    """Database connection settings for users"""
    __tablename__ = "database_connections"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Connection details
    name = Column(String(100), nullable=False)  # User-friendly name for the connection
    db_type = Column(String(20), nullable=False)  # mysql, postgresql, sqlite, etc.
    host = Column(String(255), nullable=True)
    port = Column(Integer, nullable=True)
    database_name = Column(String(100), nullable=False)
    username = Column(String(100), nullable=True)
    password = Column(Text, nullable=True)  # Encrypted in production
    
    # Additional settings
    connection_string = Column(Text, nullable=True)  # Optional custom connection string
    is_active = Column(Boolean, default=True, nullable=False)
    last_tested_at = Column(DateTime(timezone=True), nullable=True)
    last_test_status = Column(String(20), nullable=True)  # success, failed, not_tested
    
    # Schema information (auto-extracted on connection)
    schema_text = Column(Text, nullable=True)  # Formatted schema for ML model
    schema_tables = Column(Text, nullable=True)  # JSON: table names and columns
    foreign_keys = Column(Text, nullable=True)  # JSON: FK relationships
    primary_keys = Column(Text, nullable=True)  # JSON: Primary keys per table
    column_types = Column(Text, nullable=True)  # JSON: Column data types
    table_count = Column(Integer, nullable=True)  # Number of tables
    total_columns = Column(Integer, nullable=True)  # Total columns across all tables
    schema_extracted_at = Column(DateTime(timezone=True), nullable=True)  # Last schema extraction time
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="database_connections")
    
    def __repr__(self):
        return f"<DatabaseConnection(id={self.id}, name='{self.name}', db_type='{self.db_type}', user_id={self.user_id})>"
