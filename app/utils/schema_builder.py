"""
Schema Builder Utility

Provides functions to build schema text from various sources
for the NL2SQL model inference.
"""

from typing import Dict, List, Tuple, Optional
import json
from pathlib import Path


def build_schema_from_dict(
    tables_dict: Dict[str, List[str]], 
    foreign_keys: Optional[List[Tuple[str, str, str, str]]] = None
) -> Tuple[str, List[Tuple[str, str, str, str]]]:
    """
    Create schema text from a dictionary.
    Enhanced to include foreign key annotations for better accuracy.
    
    Args:
        tables_dict: {"table_name": ["col1", "col2", ...], ...}
        foreign_keys: [(from_table, from_col, to_table, to_col), ...] (optional)
    
    Returns:
        tuple: (schema_text, foreign_keys)
    
    Example:
        >>> schema_dict = {
        ...     "users": ["id", "name", "email"],
        ...     "orders": ["id", "user_id", "total"]
        ... }
        >>> fks = [("orders", "user_id", "users", "id")]
        >>> schema_text, fks = build_schema_from_dict(schema_dict, fks)
    """
    fk_list = foreign_keys or []
    
    # Build FK lookup for annotations
    fk_from_table = {}
    for from_table, from_col, to_table, to_col in fk_list:
        if from_table not in fk_from_table:
            fk_from_table[from_table] = []
        fk_from_table[from_table].append((from_col, to_table, to_col))
    
    lines = []
    for table_name in sorted(tables_dict.keys()):
        lines.append(f"TABLE {table_name}:")
        for col in tables_dict[table_name]:
            col_line = f"- {table_name}.{col}"
            
            # Add FK annotation if this column is a foreign key
            if table_name in fk_from_table:
                for fk_col, ref_table, ref_col in fk_from_table[table_name]:
                    if fk_col == col:
                        col_line += f" (references {ref_table}.{ref_col})"
                        break
            
            lines.append(col_line)
        lines.append("")
    
    return "\n".join(lines), fk_list


def parse_schema_metadata(schema_text: str) -> Tuple[Dict[str, set], Dict[str, List[str]]]:
    """
    Parse schema text into structured metadata.
    Enhanced to handle FK annotations.
    
    Schema format (simple text):
        TABLE table_name:
        - table_name.column1
        - table_name.column2 (references other_table.id)
        
        TABLE another_table:
        - another_table.column1
    
    Returns:
        tuple: (tables, column_to_tables)
            - tables: dict mapping table_name -> set of column names
            - column_to_tables: dict mapping column_name -> list of tables that have it
    """
    tables = {}
    column_to_tables = {}
    current_table = None

    for line in schema_text.splitlines():
        line = line.strip()
        if not line:
            continue

        if line.startswith("TABLE"):
            current_table = line.replace("TABLE", "").replace(":", "").strip()
            tables[current_table] = set()

        elif line.startswith("-") and current_table:
            col = line.replace("-", "").strip()
            
            # Remove FK annotation if present
            if " (references " in col:
                col = col.split(" (references ")[0]
            
            if "." in col:
                table, column = col.split(".", 1)
                tables[table].add(column)
                
                # Track which tables have which columns
                if column not in column_to_tables:
                    column_to_tables[column] = []
                column_to_tables[column].append(table)

    return tables, column_to_tables


def load_schema_from_spider_json(
    db_id: str,
    tables_json_path: str
) -> Tuple[str, List[Tuple[str, str, str, str]]]:
    """
    Load schema metadata from Spider's tables.json file.
    
    Args:
        db_id: Database identifier
        tables_json_path: Path to tables.json file
    
    Returns:
        tuple: (schema_text, foreign_keys)
            - schema_text: Formatted schema string (matches training format exactly)
            - foreign_keys: List of (table1, col1, table2, col2) tuples
    """
    with open(tables_json_path) as f:
        all_dbs = json.load(f)
    
    # Find our database
    db = None
    for d in all_dbs:
        if d.get('db_id') == db_id:
            db = d
            break
    
    if not db:
        raise ValueError(f"Database '{db_id}' not found in {tables_json_path}")
    
    # Extract table names and columns (use ORIGINAL names to match training!)
    table_names = db['table_names_original']
    column_names = db['column_names_original']  # Format: [[table_idx, col_name], ...]
    
    # Build schema text (exactly matching training format)
    schema_lines = []
    table_to_cols = {i: [] for i in range(len(table_names))}
    
    for col_table_id, col_name in column_names:
        if col_table_id >= 0:  # ignore '*'
            table_to_cols[col_table_id].append(col_name)
    
    for table_id, table_name in enumerate(table_names):
        schema_lines.append(f"TABLE {table_name}:")
        for col in table_to_cols[table_id]:
            schema_lines.append(f"- {table_name}.{col}")
        schema_lines.append("")  # blank line between tables
    
    schema_text = "\n".join(schema_lines)
    
    # Extract foreign keys
    foreign_keys_raw = db.get('foreign_keys', [])
    foreign_keys = []
    
    for fk_col_idx, ref_col_idx in foreign_keys_raw:
        # Get table and column info for both sides
        fk_table_idx, fk_col_name = column_names[fk_col_idx]
        ref_table_idx, ref_col_name = column_names[ref_col_idx]
        
        fk_table = table_names[fk_table_idx]
        ref_table = table_names[ref_table_idx]
        
        foreign_keys.append((fk_table, fk_col_name, ref_table, ref_col_name))
    
    return schema_text, foreign_keys


def format_schema_from_connection(db_connection) -> Tuple[str, List[Tuple[str, str, str, str]]]:
    """
    Extract schema text and foreign keys from a DatabaseConnection model instance.
    
    Args:
        db_connection: DatabaseConnection model instance with schema data
    
    Returns:
        (schema_text, foreign_keys)
    """
    # Get schema text (already formatted for ML model)
    schema_text = db_connection.schema_text or ""
    
    # Parse foreign keys from JSON
    foreign_keys = []
    if db_connection.foreign_keys:
        try:
            fk_list = json.loads(db_connection.foreign_keys)
            foreign_keys = [tuple(fk) for fk in fk_list]
        except:
            pass
    
    return schema_text, foreign_keys


def get_schema_summary(db_connection) -> Dict:
    """
    Get a summary of the database schema from a DatabaseConnection instance.
    
    Args:
        db_connection: DatabaseConnection model instance
    
    Returns:
        Dictionary with schema summary
    """
    tables = {}
    if db_connection.schema_tables:
        try:
            tables = json.loads(db_connection.schema_tables)
        except:
            pass
    
    foreign_keys = []
    if db_connection.foreign_keys:
        try:
            fk_list = json.loads(db_connection.foreign_keys)
            foreign_keys = [tuple(fk) for fk in fk_list]
        except:
            pass
    
    primary_keys = {}
    if db_connection.primary_keys:
        try:
            primary_keys = json.loads(db_connection.primary_keys)
        except:
            pass
    
    return {
        "database_name": db_connection.database_name,
        "db_type": db_connection.db_type,
        "table_count": db_connection.table_count or 0,
        "total_columns": db_connection.total_columns or 0,
        "tables": tables,
        "foreign_keys": foreign_keys,
        "primary_keys": primary_keys,
        "schema_extracted_at": db_connection.schema_extracted_at
    }
