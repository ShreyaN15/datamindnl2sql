"""
Schema Inference Service

Automatically extracts and structures database schema information including:
- Table names
- Column names and types
- Primary keys
- Foreign key relationships (auto-detected using multiple techniques)
- Column relationships and patterns

The schema is formatted exactly as the ML model expects for optimal NL2SQL performance.
"""

from sqlalchemy import create_engine, inspect, MetaData, Table
from sqlalchemy.engine import Engine
from typing import Dict, List, Tuple, Optional, Set
import re
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class SchemaInferenceService:
    """
    Intelligent schema inference and structuring service.
    
    Uses multiple techniques to detect relationships:
    1. Explicit foreign key constraints (metadata)
    2. Naming convention analysis (id, user_id pattern matching)
    3. Column type and name similarity
    4. Primary key references
    """
    
    def __init__(self):
        self.naming_patterns = [
            # Pattern: column named "X_id" likely references table "X" column "id"
            (r'^(.+)_id$', lambda match: (match.group(1), 'id')),
            # Pattern: column named "Xid" likely references table "X" column "id"  
            (r'^(.+)id$', lambda match: (match.group(1), 'id')),
            # Pattern: column named "X_ID" likely references table "X" column "ID"
            (r'^(.+)_ID$', lambda match: (match.group(1), 'ID')),
        ]
    
    def infer_schema_from_connection(
        self,
        connection_string: str,
        db_type: str,
        connect_args: Optional[Dict] = None
    ) -> Dict:
        """
        Extract complete schema information from a database connection.
        
        Args:
            connection_string: SQLAlchemy connection string
            db_type: Database type (mysql, postgresql, sqlite, etc.)
            connect_args: Additional connection arguments
        
        Returns:
            Dictionary containing:
                - schema_text: Formatted schema for ML model
                - tables: Dict of table_name -> column list
                - columns: Dict of table_name -> column details
                - foreign_keys: List of (from_table, from_col, to_table, to_col)
                - primary_keys: Dict of table_name -> primary key columns
                - column_types: Dict of (table, column) -> type
                - table_count: Number of tables
                - total_columns: Total number of columns
        """
        try:
            # Create engine and inspector
            engine = create_engine(
                connection_string,
                connect_args=connect_args or {}
            )
            inspector = inspect(engine)
            
            # Extract basic schema info
            table_names = inspector.get_table_names()
            
            if not table_names:
                return self._empty_schema()
            
            # Collect detailed information
            tables = {}
            columns_detail = {}
            primary_keys = {}
            column_types = {}
            
            for table_name in table_names:
                # Get columns
                columns = inspector.get_columns(table_name)
                column_names = [col['name'] for col in columns]
                tables[table_name] = column_names
                
                # Store column details
                columns_detail[table_name] = columns
                
                # Store column types
                for col in columns:
                    column_types[(table_name, col['name'])] = str(col['type'])
                
                # Get primary keys
                pk_constraint = inspector.get_pk_constraint(table_name)
                if pk_constraint and pk_constraint.get('constrained_columns'):
                    primary_keys[table_name] = pk_constraint['constrained_columns']
            
            # Extract foreign keys using multiple methods
            foreign_keys = self._extract_foreign_keys(
                inspector, 
                table_names, 
                tables, 
                primary_keys,
                column_types
            )
            
            # Generate schema text in ML model format
            schema_text = self._format_schema_for_ml(tables, foreign_keys)
            
            # Calculate statistics
            total_columns = sum(len(cols) for cols in tables.values())
            
            engine.dispose()
            
            return {
                'schema_text': schema_text,
                'tables': tables,
                'columns': columns_detail,
                'foreign_keys': foreign_keys,
                'primary_keys': primary_keys,
                'column_types': column_types,
                'table_count': len(table_names),
                'total_columns': total_columns,
                'db_type': db_type
            }
            
        except Exception as e:
            logger.error(f"Schema inference failed: {e}")
            raise
    
    def _extract_foreign_keys(
        self,
        inspector,
        table_names: List[str],
        tables: Dict[str, List[str]],
        primary_keys: Dict[str, List[str]],
        column_types: Dict[Tuple[str, str], str]
    ) -> List[Tuple[str, str, str, str]]:
        """
        Extract foreign key relationships using multiple detection methods.
        
        Returns:
            List of (from_table, from_col, to_table, to_col) tuples
        """
        foreign_keys = []
        detected_fks = set()  # Track to avoid duplicates
        
        # Method 1: Explicit foreign key constraints (most reliable)
        for table_name in table_names:
            try:
                fks = inspector.get_foreign_keys(table_name)
                for fk in fks:
                    constrained_cols = fk.get('constrained_columns', [])
                    referred_table = fk.get('referred_table')
                    referred_cols = fk.get('referred_columns', [])
                    
                    # Create FK relationships
                    for from_col, to_col in zip(constrained_cols, referred_cols):
                        fk_tuple = (table_name, from_col, referred_table, to_col)
                        if fk_tuple not in detected_fks:
                            foreign_keys.append(fk_tuple)
                            detected_fks.add(fk_tuple)
                            logger.info(f"Found FK (explicit): {fk_tuple}")
            except Exception as e:
                logger.warning(f"Could not get FKs for {table_name}: {e}")
        
        # Method 2: Naming convention analysis (heuristic)
        inferred_fks = self._infer_fks_from_naming(
            tables, 
            primary_keys,
            column_types,
            detected_fks
        )
        foreign_keys.extend(inferred_fks)
        
        return foreign_keys
    
    def _infer_fks_from_naming(
        self,
        tables: Dict[str, List[str]],
        primary_keys: Dict[str, List[str]],
        column_types: Dict[Tuple[str, str], str],
        existing_fks: Set[Tuple[str, str, str, str]]
    ) -> List[Tuple[str, str, str, str]]:
        """
        Infer foreign keys based on naming conventions and column patterns.
        
        Common patterns:
        - Column "user_id" likely references "users.id" or "user.id"
        - Column "product_id" likely references "products.id" or "product.id"
        - Column "customer_ID" likely references "customer.ID"
        """
        inferred_fks = []
        table_names_lower = {t.lower(): t for t in tables.keys()}
        
        for table_name, columns in tables.items():
            for col_name in columns:
                col_lower = col_name.lower()
                
                # Check each naming pattern
                for pattern, extractor in self.naming_patterns:
                    match = re.match(pattern, col_name, re.IGNORECASE)
                    if match:
                        # Extract potential referenced table and column
                        potential_table, potential_col = extractor(match)
                        
                        # Try to find matching table (handle plural/singular)
                        referenced_table = self._find_referenced_table(
                            potential_table,
                            table_names_lower,
                            tables.keys()
                        )
                        
                        if referenced_table:
                            # Check if referenced table has matching column
                            referenced_cols = tables.get(referenced_table, [])
                            
                            # Find matching column (case-insensitive)
                            matching_col = None
                            for ref_col in referenced_cols:
                                if ref_col.lower() == potential_col.lower():
                                    matching_col = ref_col
                                    break
                            
                            if matching_col:
                                # Validate this is likely a FK (type compatibility)
                                from_type = column_types.get((table_name, col_name))
                                to_type = column_types.get((referenced_table, matching_col))
                                
                                if self._types_compatible(from_type, to_type):
                                    fk_tuple = (table_name, col_name, referenced_table, matching_col)
                                    
                                    # Only add if not already detected
                                    if fk_tuple not in existing_fks:
                                        inferred_fks.append(fk_tuple)
                                        logger.info(f"Inferred FK (naming): {fk_tuple}")
                        
                        break  # Stop checking patterns for this column
        
        return inferred_fks
    
    def _find_referenced_table(
        self,
        potential_name: str,
        table_names_lower: Dict[str, str],
        actual_tables: List[str]
    ) -> Optional[str]:
        """
        Find the actual table name from a potential reference.
        
        Handles:
        - Exact match
        - Plural/singular variations
        - Case differences
        """
        potential_lower = potential_name.lower()
        
        # Direct match
        if potential_lower in table_names_lower:
            return table_names_lower[potential_lower]
        
        # Try plural variations
        plural_candidates = [
            potential_lower + 's',      # user -> users
            potential_lower + 'es',     # address -> addresses
            potential_lower[:-1] if potential_lower.endswith('s') else None,  # users -> user
        ]
        
        for candidate in plural_candidates:
            if candidate and candidate in table_names_lower:
                return table_names_lower[candidate]
        
        # Try removing common prefixes/suffixes
        if potential_lower.endswith('_id'):
            base = potential_lower[:-3]
            if base in table_names_lower:
                return table_names_lower[base]
        
        return None
    
    def _types_compatible(self, type1: Optional[str], type2: Optional[str]) -> bool:
        """
        Check if two column types are compatible for FK relationship.
        """
        if not type1 or not type2:
            return True  # Assume compatible if we can't determine
        
        # Normalize types
        t1 = str(type1).upper()
        t2 = str(type2).upper()
        
        # Integer types are compatible with each other
        int_types = ['INTEGER', 'INT', 'BIGINT', 'SMALLINT', 'TINYINT', 'SERIAL', 'BIGSERIAL']
        if any(it in t1 for it in int_types) and any(it in t2 for it in int_types):
            return True
        
        # String types are compatible with each other
        str_types = ['VARCHAR', 'CHAR', 'TEXT', 'STRING']
        if any(st in t1 for st in str_types) and any(st in t2 for st in str_types):
            return True
        
        # UUID types
        if 'UUID' in t1 and 'UUID' in t2:
            return True
        
        return False
    
    def _format_schema_for_ml(
        self,
        tables: Dict[str, List[str]],
        foreign_keys: List[Tuple[str, str, str, str]]
    ) -> str:
        """
        Format schema in the exact format expected by the ML model.
        Enhanced with better structure for improved accuracy.
        
        Format:
            TABLE table_name:
            - table_name.column1
            - table_name.column2
            
            TABLE another_table:
            - another_table.column1
        """
        lines = []
        
        # Build FK lookup for adding relationship context
        fk_from_table = {}  # table -> list of (col, ref_table, ref_col)
        for from_table, from_col, to_table, to_col in foreign_keys:
            if from_table not in fk_from_table:
                fk_from_table[from_table] = []
            fk_from_table[from_table].append((from_col, to_table, to_col))
        
        for table_name in sorted(tables.keys()):
            lines.append(f"TABLE {table_name}:")
            
            # Add columns with FK annotations
            for column_name in tables[table_name]:
                col_line = f"- {table_name}.{column_name}"
                
                # Check if this column is a foreign key
                if table_name in fk_from_table:
                    for fk_col, ref_table, ref_col in fk_from_table[table_name]:
                        if fk_col == column_name:
                            col_line += f" (references {ref_table}.{ref_col})"
                            break
                
                lines.append(col_line)
            
            lines.append("")  # Blank line between tables
        
        return "\n".join(lines).strip()
    
    def _empty_schema(self) -> Dict:
        """Return empty schema structure"""
        return {
            'schema_text': '',
            'tables': {},
            'columns': {},
            'foreign_keys': [],
            'primary_keys': {},
            'column_types': {},
            'table_count': 0,
            'total_columns': 0,
            'db_type': 'unknown'
        }
    
    def format_foreign_keys_for_storage(
        self,
        foreign_keys: List[Tuple[str, str, str, str]]
    ) -> str:
        """
        Convert foreign key list to compact JSON string for database storage.
        
        Format: [["table1", "col1", "table2", "col2"], ...]
        """
        import json
        return json.dumps([list(fk) for fk in foreign_keys])
    
    def parse_foreign_keys_from_storage(
        self,
        fk_json: str
    ) -> List[Tuple[str, str, str, str]]:
        """
        Parse foreign keys from stored JSON string.
        """
        import json
        if not fk_json:
            return []
        try:
            fk_list = json.loads(fk_json)
            return [tuple(fk) for fk in fk_list]
        except:
            return []
