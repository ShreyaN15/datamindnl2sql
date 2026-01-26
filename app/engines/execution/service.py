"""
SQL Execution Engine
Executes SQL queries safely against user databases and returns results
"""

from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)


class QueryExecutionService:
    """Service for executing SQL queries safely"""
    
    def __init__(self):
        self.max_rows = 1000  # Limit results to prevent memory issues
        self.timeout_seconds = 30  # Query timeout
    
    def execute_query(
        self,
        sql_query: str,
        db_type: str,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str
    ) -> Dict[str, Any]:
        """
        Execute a SQL query and return results
        
        Args:
            sql_query: SQL query to execute
            db_type: Database type (postgresql, mysql, sqlite)
            host: Database host
            port: Database port
            database: Database name
            username: Database username
            password: Database password
            
        Returns:
            Dictionary with execution results or error information
        """
        try:
            # Create database connection
            connection_string = self._build_connection_string(
                db_type, host, port, database, username, password
            )
            
            engine = create_engine(
                connection_string,
                pool_pre_ping=True,
                connect_args={'connect_timeout': self.timeout_seconds}
            )
            
            # Execute query
            with engine.connect() as connection:
                # Set timeout
                if db_type == 'postgresql':
                    connection.execute(text(f"SET statement_timeout = {self.timeout_seconds * 1000}"))
                elif db_type == 'mysql':
                    connection.execute(text(f"SET SESSION max_execution_time = {self.timeout_seconds * 1000}"))
                
                # Execute the actual query
                result = connection.execute(text(sql_query))
                
                # Fetch results
                rows = result.fetchmany(self.max_rows)
                columns = list(result.keys()) if result.returns_rows else []
                
                # Convert rows to list of dictionaries
                data = []
                for row in rows:
                    data.append(dict(zip(columns, row)))
                
                # Check if there are more rows
                has_more = len(rows) == self.max_rows
                
                return {
                    'success': True,
                    'data': data,
                    'columns': columns,
                    'row_count': len(data),
                    'has_more': has_more,
                    'error': None
                }
                
        except SQLAlchemyError as e:
            logger.error(f"SQL execution error: {str(e)}")
            return {
                'success': False,
                'data': [],
                'columns': [],
                'row_count': 0,
                'has_more': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error during query execution: {str(e)}")
            return {
                'success': False,
                'data': [],
                'columns': [],
                'row_count': 0,
                'has_more': False,
                'error': f"Unexpected error: {str(e)}"
            }
        finally:
            # Clean up engine
            if 'engine' in locals():
                engine.dispose()
    
    def _build_connection_string(
        self,
        db_type: str,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str
    ) -> str:
        """Build SQLAlchemy connection string"""
        if db_type == 'postgresql':
            return f"postgresql://{username}:{password}@{host}:{port}/{database}"
        elif db_type == 'mysql':
            return f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"
        elif db_type == 'sqlite':
            return f"sqlite:///{database}"
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    def analyze_query_type(self, sql_query: str) -> str:
        """
        Analyze SQL query to determine if it's suitable for visualization
        
        Returns: 'select', 'aggregate', 'insert', 'update', 'delete', 'other'
        """
        query_upper = sql_query.strip().upper()
        
        if query_upper.startswith('SELECT'):
            # Check for aggregation functions
            if any(agg in query_upper for agg in ['COUNT(', 'SUM(', 'AVG(', 'MIN(', 'MAX(', 'GROUP BY']):
                return 'aggregate'
            return 'select'
        elif query_upper.startswith('INSERT'):
            return 'insert'
        elif query_upper.startswith('UPDATE'):
            return 'update'
        elif query_upper.startswith('DELETE'):
            return 'delete'
        else:
            return 'other'
    
    def is_visualizable(self, data: List[Dict], columns: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Determine if query results are suitable for visualization
        
        Returns:
            Tuple of (is_visualizable, suggested_chart_type)
        """
        if not data or not columns:
            return False, None
        
        if len(data) > 100:
            # Too many rows for effective visualization
            return False, None
        
        # Analyze column types
        numeric_cols = []
        text_cols = []
        
        for col in columns:
            sample_value = data[0].get(col)
            if isinstance(sample_value, (int, float)):
                numeric_cols.append(col)
            else:
                text_cols.append(col)
        
        # Determine chart type
        if len(columns) == 2 and len(text_cols) == 1 and len(numeric_cols) == 1:
            # One categorical, one numeric - good for bar chart
            return True, 'bar'
        elif len(numeric_cols) >= 2:
            # Multiple numeric columns - good for line chart
            return True, 'line'
        elif len(columns) == 1 and len(numeric_cols) == 1:
            # Single numeric column - good for histogram
            return True, 'histogram'
        elif len(text_cols) >= 1 and len(numeric_cols) >= 1:
            # Mixed - default to bar chart
            return True, 'bar'
        
        return False, None


# Singleton instance
_execution_service = None

def get_execution_service() -> QueryExecutionService:
    """Get singleton instance of QueryExecutionService"""
    global _execution_service
    if _execution_service is None:
        _execution_service = QueryExecutionService()
    return _execution_service
