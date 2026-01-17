"""
Database Connection Service

Service for managing and testing database connections
"""

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, Optional, Tuple
import logging
from datetime import datetime

from app.schemas.db import DatabaseType

logger = logging.getLogger(__name__)


class DatabaseConnectionService:
    """Service for testing and managing database connections"""
    
    @staticmethod
    def build_connection_string(
        db_type: str,
        host: Optional[str],
        port: Optional[int],
        database_name: str,
        username: Optional[str],
        password: Optional[str],
        custom_string: Optional[str] = None
    ) -> str:
        """
        Build a connection string from connection details.
        
        Args:
            db_type: Type of database (mysql, postgresql, etc.)
            host: Database host
            port: Database port
            database_name: Database name
            username: Database username
            password: Database password
            custom_string: Custom connection string (overrides other params)
        
        Returns:
            Connection string
        """
        if custom_string:
            return custom_string
        
        # Default ports
        default_ports = {
            DatabaseType.MYSQL: 3306,
            DatabaseType.POSTGRESQL: 5432,
            DatabaseType.MSSQL: 1433,
            DatabaseType.ORACLE: 1521
        }
        
        port = port or default_ports.get(db_type, 3306)
        
        if db_type == DatabaseType.MYSQL:
            driver = "mysql+pymysql"
            if username and password:
                conn_str = f"{driver}://{username}:{password}@{host}:{port}/{database_name}"
            else:
                conn_str = f"{driver}://{host}:{port}/{database_name}"
                
        elif db_type == DatabaseType.POSTGRESQL:
            driver = "postgresql+psycopg2"
            if username and password:
                conn_str = f"{driver}://{username}:{password}@{host}:{port}/{database_name}"
            else:
                conn_str = f"{driver}://{host}:{port}/{database_name}"
                
        elif db_type == DatabaseType.SQLITE:
            # SQLite uses file path
            conn_str = f"sqlite:///{database_name}"
            
        elif db_type == DatabaseType.MSSQL:
            driver = "mssql+pyodbc"
            if username and password:
                conn_str = f"{driver}://{username}:{password}@{host}:{port}/{database_name}?driver=ODBC+Driver+17+for+SQL+Server"
            else:
                conn_str = f"{driver}://{host}:{port}/{database_name}?driver=ODBC+Driver+17+for+SQL+Server"
                
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
        
        return conn_str
    
    @staticmethod
    def test_connection(connection_string: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Test a database connection.
        
        Args:
            connection_string: Database connection string
        
        Returns:
            Tuple of (success: bool, message: str, details: dict)
        """
        try:
            # Create engine with appropriate timeout settings
            if "sqlite" in connection_string.lower():
                # SQLite doesn't support connect_timeout in connect_args
                engine = create_engine(
                    connection_string,
                    pool_pre_ping=True
                )
            else:
                engine = create_engine(
                    connection_string,
                    connect_args={"connect_timeout": 10},
                    pool_pre_ping=True
                )
            
            # Try to connect and execute a simple query
            with engine.connect() as connection:
                # Test basic connection
                result = connection.execute(text("SELECT 1"))
                result.fetchone()
                
                # Get database version if possible
                details = {}
                try:
                    version_result = connection.execute(text("SELECT VERSION()"))
                    version = version_result.fetchone()
                    if version:
                        details["database_version"] = str(version[0])
                except:
                    pass
                
                # Try to get table count
                try:
                    if "mysql" in connection_string.lower():
                        tables_result = connection.execute(text("SHOW TABLES"))
                        details["tables_count"] = len(tables_result.fetchall())
                    elif "postgresql" in connection_string.lower():
                        tables_result = connection.execute(text(
                            "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"
                        ))
                        details["tables_count"] = tables_result.fetchone()[0]
                    elif "sqlite" in connection_string.lower():
                        tables_result = connection.execute(text(
                            "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
                        ))
                        details["tables_count"] = tables_result.fetchone()[0]
                except:
                    pass
            
            engine.dispose()
            logger.info(f"Database connection test successful")
            return True, "Connection successful", details
            
        except SQLAlchemyError as e:
            error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
            logger.error(f"Database connection test failed: {error_msg}")
            return False, f"Connection failed: {error_msg}", None
            
        except Exception as e:
            logger.error(f"Unexpected error during connection test: {str(e)}")
            return False, f"Unexpected error: {str(e)}", None
    
    @staticmethod
    def get_schema_info(connection_string: str) -> Optional[Dict]:
        """
        Get schema information from a database connection.
        
        Args:
            connection_string: Database connection string
        
        Returns:
            Dictionary with schema information (tables and columns)
        """
        try:
            # Create engine with appropriate timeout settings
            if "sqlite" in connection_string.lower():
                engine = create_engine(connection_string)
            else:
                engine = create_engine(
                    connection_string,
                    connect_args={"connect_timeout": 10}
                )
            
            schema_info = {"tables": {}}
            
            with engine.connect() as connection:
                if "mysql" in connection_string.lower():
                    # Get tables
                    tables_result = connection.execute(text("SHOW TABLES"))
                    tables = [row[0] for row in tables_result.fetchall()]
                    
                    # Get columns for each table
                    for table in tables:
                        columns_result = connection.execute(text(f"DESCRIBE {table}"))
                        columns = [row[0] for row in columns_result.fetchall()]
                        schema_info["tables"][table] = columns
                        
                elif "postgresql" in connection_string.lower():
                    # Get tables
                    tables_result = connection.execute(text(
                        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
                    ))
                    tables = [row[0] for row in tables_result.fetchall()]
                    
                    # Get columns for each table
                    for table in tables:
                        columns_result = connection.execute(text(
                            f"SELECT column_name FROM information_schema.columns "
                            f"WHERE table_name = '{table}' AND table_schema = 'public'"
                        ))
                        columns = [row[0] for row in columns_result.fetchall()]
                        schema_info["tables"][table] = columns
                
                elif "sqlite" in connection_string.lower():
                    # Get tables
                    tables_result = connection.execute(text(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                    ))
                    tables = [row[0] for row in tables_result.fetchall()]
                    
                    # Get columns for each table
                    for table in tables:
                        columns_result = connection.execute(text(f"PRAGMA table_info({table})"))
                        columns = [row[1] for row in columns_result.fetchall()]
                        schema_info["tables"][table] = columns
            
            engine.dispose()
            return schema_info
            
        except Exception as e:
            logger.error(f"Failed to get schema info: {str(e)}")
            return None
