"""
SQL Validator and Sanitizer

Validates and corrects SQL queries against database schema.
Handles case-insensitive matching, auto-qualification, and schema enforcement.
"""

import re
from typing import Dict, List, Set, Tuple, Optional
from sqlglot import exp, parse_one
from sqlglot.errors import ParseError


class SQLValidator:
    """
    SQL Sanitizer: Validates and corrects SQL against schema.
    
    Key features:
    1. Case-insensitive column matching
    2. Smart auto-qualification (only when necessary)
    3. Detects columns from wrong tables (actual errors)
    4. Validates JOIN conditions against foreign keys
    5. Logical query validation
    """
    
    def __init__(
        self, 
        schema_tables: Dict[str, Set[str]], 
        column_to_tables: Dict[str, List[str]], 
        foreign_keys: Optional[List[Tuple[str, str, str, str]]] = None
    ):
        """
        Initialize the validator.
        
        Args:
            schema_tables: dict mapping table_name -> set of column names
            column_to_tables: dict mapping column_name -> list of tables that have it
            foreign_keys: List of (table1, col1, table2, col2) tuples
        """
        self.schema_tables = schema_tables
        self.column_to_tables = column_to_tables
        self.all_columns = set(column_to_tables.keys())
        
        # Create case-insensitive lookup maps
        self.column_case_map = {}  # lowercase -> actual case
        for col in self.all_columns:
            self.column_case_map[col.lower()] = col
        
        self.table_column_map = {}  # (table, lowercase_col) -> actual_col
        for table, cols in self.schema_tables.items():
            for col in cols:
                self.table_column_map[(table, col.lower())] = col
        
        # Store foreign key relationships
        self.foreign_keys = foreign_keys or []
        
        # Build reverse FK map for validation
        self.valid_joins = {}  # (table1, table2) -> [(col1_in_t1, col2_in_t2), ...]
        for t1, c1, t2, c2 in self.foreign_keys:
            # Store in both directions for easier lookup
            key = (t1, t2)
            if key not in self.valid_joins:
                self.valid_joins[key] = []
            self.valid_joins[key].append((c1, c2))
            
            # Reverse direction
            key_rev = (t2, t1)
            if key_rev not in self.valid_joins:
                self.valid_joins[key_rev] = []
            self.valid_joins[key_rev].append((c2, c1))
    
    def _normalize_column_name(self, col_name: str) -> str:
        """Get the correct case for a column name"""
        return self.column_case_map.get(col_name.lower(), col_name)
    
    def _column_exists_in_table(self, table: str, col_name: str) -> bool:
        """Check if column exists in table (case-insensitive)"""
        if table not in self.schema_tables:
            return False
        return (table, col_name.lower()) in self.table_column_map
    
    def _get_correct_column_name(self, table: str, col_name: str) -> str:
        """Get correct case for column in specific table"""
        return self.table_column_map.get((table, col_name.lower()), col_name)
    
    def _apply_simple_fixes(self, sql: str) -> str:
        """Apply simple pattern-based fixes before parsing"""
        # Fix 1: Date year comparisons (WHERE date_col = YYYY → WHERE date_col LIKE "%YYYY%")
        sql = re.sub(
            r'WHERE\s+(\w+)\s*=\s*(20\d{2})\b',
            r'WHERE \1 LIKE "%\2%"',
            sql,
            flags=re.IGNORECASE
        )
        
        # Fix 2: Remove unnecessary GROUP BY with COUNT(*)
        if 'COUNT(*)' in sql.upper() and 'GROUP BY' in sql.upper():
            if re.search(r'GROUP BY\s+\w*id\b', sql, re.IGNORECASE):
                if sql.upper().count('SELECT') == 1 and not any(
                    func in sql.upper() for func in ['AVG', 'SUM', 'MAX', 'MIN']
                ):
                    sql = re.sub(r'\s+GROUP BY\s+\w+', '', sql, flags=re.IGNORECASE)
        
        return sql
    
    def validate_and_fix(self, sql: str) -> Tuple[bool, str, List[str]]:
        """
        Validate SQL and attempt to fix common issues.
        
        Returns:
            tuple: (is_valid, corrected_sql, errors)
                - is_valid: Whether the SQL is valid (no errors)
                - corrected_sql: The corrected SQL query
                - errors: List of error/warning messages
        """
        errors = []
        
        # Apply simple pattern-based fixes first
        sql = self._apply_simple_fixes(sql)
        
        # Step 1: Parse with sqlglot
        try:
            parsed = parse_one(sql, read='sqlite')
        except ParseError as e:
            errors.append(f"ERROR: Syntax error: {str(e)}")
            return False, sql, errors
        
        # Step 2: Extract referenced tables and columns
        referenced_tables = set()
        referenced_columns = {}  # column -> contexts where it appears
        table_aliases = {}  # alias -> real table name
        reverse_aliases = {}  # real table -> alias
        join_conditions = []  # List of (table1, col1, table2, col2)
        
        # Find all table references
        for table in parsed.find_all(exp.Table):
            table_name = table.name
            referenced_tables.add(table_name)
            
            # Track aliases
            if table.alias:
                alias_name = table.alias
                table_aliases[alias_name] = table_name
                reverse_aliases[table_name] = alias_name
            
            # Validate table exists in schema
            if table_name not in self.schema_tables:
                errors.append(f"ERROR: Table '{table_name}' not in schema")
        
        # Extract JOIN conditions
        for join in parsed.find_all(exp.Join):
            on_clause = join.args.get('on')
            if on_clause and isinstance(on_clause, exp.EQ):
                left = on_clause.left if hasattr(on_clause, 'left') else on_clause.this
                right = on_clause.right if hasattr(on_clause, 'right') else on_clause.expression
                
                if isinstance(left, exp.Column) and isinstance(right, exp.Column):
                    left_table = left.table if hasattr(left, 'table') and left.table else None
                    right_table = right.table if hasattr(right, 'table') and right.table else None
                    left_col = left.name
                    right_col = right.name
                    
                    # Resolve aliases
                    if left_table in table_aliases:
                        left_table = table_aliases[left_table]
                    if right_table in table_aliases:
                        right_table = table_aliases[right_table]
                    
                    if left_table and right_table:
                        join_conditions.append((left_table, left_col, right_table, right_col))
        
        # Find all column references
        for col in parsed.find_all(exp.Column):
            col_name = col.name
            table_ref = col.table if hasattr(col, 'table') and col.table else None
            
            # Resolve alias to real table name
            if table_ref and table_ref in table_aliases:
                table_ref = table_aliases[table_ref]
            
            # Normalize column name (fix case)
            normalized_col = self._normalize_column_name(col_name)
            
            if normalized_col not in self.all_columns:
                if col_name.lower() in self.column_case_map:
                    errors.append(f"Fixed column case: '{col_name}' -> '{normalized_col}'")
                    col_name = normalized_col
                else:
                    errors.append(f"ERROR: Column '{col_name}' not in schema")
                    continue
            else:
                col_name = normalized_col
            
            if col_name not in referenced_columns:
                referenced_columns[col_name] = []
            referenced_columns[col_name].append({
                'node': col,
                'qualified': table_ref is not None,
                'table': table_ref,
                'original_name': col.name
            })
        
        # Step 3: Validate JOIN conditions
        self._validate_join_conditions(join_conditions, errors)
        
        # Step 4: Smart column qualification
        self._qualify_columns(
            referenced_columns, 
            referenced_tables, 
            table_aliases, 
            errors
        )
        
        # Step 5: Generate corrected SQL
        corrected_sql = parsed.sql(dialect='sqlite')
        
        # Step 6: Post-processing cleanup
        corrected_sql = self._post_process_sql(corrected_sql)
        
        # Check if valid (no ERROR markers)
        is_valid = len([e for e in errors if e.startswith('ERROR:')]) == 0
        
        return is_valid, corrected_sql, errors
    
    def _validate_join_conditions(
        self, 
        join_conditions: List[Tuple[str, str, str, str]], 
        errors: List[str]
    ):
        """Validate JOIN conditions against schema and foreign keys"""
        for t1, c1, t2, c2 in join_conditions:
            # Check if columns exist in their respective tables
            c1_exists = self._column_exists_in_table(t1, c1)
            c2_exists = self._column_exists_in_table(t2, c2)
            
            if not c1_exists:
                correct_c1 = self._get_correct_column_name(t1, c1)
                if correct_c1 != c1 and self._column_exists_in_table(t1, correct_c1):
                    errors.append(f"Fixed JOIN column case: '{t1}.{c1}' -> '{t1}.{correct_c1}'")
                else:
                    errors.append(f"ERROR: Column '{c1}' does not exist in table '{t1}' (used in JOIN)")
            
            if not c2_exists:
                correct_c2 = self._get_correct_column_name(t2, c2)
                if correct_c2 != c2 and self._column_exists_in_table(t2, correct_c2):
                    errors.append(f"Fixed JOIN column case: '{t2}.{c2}' -> '{t2}.{correct_c2}'")
                else:
                    errors.append(f"ERROR: Column '{c2}' does not exist in table '{t2}' (used in JOIN)")
            
            # Validate against foreign keys
            if c1_exists and c2_exists:
                self._validate_fk_relationship(t1, c1, t2, c2, errors)
    
    def _validate_fk_relationship(
        self, 
        t1: str, 
        c1: str, 
        t2: str, 
        c2: str, 
        errors: List[str]
    ):
        """Validate if JOIN uses correct foreign key columns"""
        join_key = (t1, t2)
        
        if join_key in self.valid_joins:
            valid_pairs = self.valid_joins[join_key]
            actual_c1 = self._get_correct_column_name(t1, c1)
            actual_c2 = self._get_correct_column_name(t2, c2)
            
            is_valid_fk = any(
                actual_c1.lower() == fk_c1.lower() and actual_c2.lower() == fk_c2.lower()
                for fk_c1, fk_c2 in valid_pairs
            )
            
            if not is_valid_fk:
                valid_cols_str = ' or '.join([f"({fk1}, {fk2})" for fk1, fk2 in valid_pairs])
                errors.append(
                    f"ERROR: Invalid JOIN between '{t1}' and '{t2}' - "
                    f"used columns ({actual_c1}, {actual_c2}) but valid foreign keys are: {valid_cols_str}"
                )
    
    def _qualify_columns(
        self, 
        referenced_columns: Dict[str, List[dict]], 
        referenced_tables: Set[str],
        table_aliases: Dict[str, str],
        errors: List[str]
    ):
        """Smart column qualification - only when necessary"""
        single_table_query = len(referenced_tables) == 1
        single_table_name = list(referenced_tables)[0] if single_table_query else None
        
        for col_name, contexts in referenced_columns.items():
            possible_tables = self.column_to_tables.get(col_name, [])
            
            for ctx in contexts:
                if not ctx['qualified']:
                    # Column is not qualified
                    if single_table_query:
                        # Single table query
                        if col_name in self.schema_tables.get(single_table_name, set()):
                            continue  # Column is in the table, no need to qualify
                        else:
                            # Column NOT in the table - ERROR
                            if len(possible_tables) == 1:
                                errors.append(
                                    f"ERROR: Column '{col_name}' from table '{possible_tables[0]}' "
                                    f"used but table '{single_table_name}' is in FROM clause - missing JOIN?"
                                )
                                ctx['node'].set('table', possible_tables[0])
                            else:
                                errors.append(f"ERROR: Column '{col_name}' not in table '{single_table_name}'")
                    else:
                        # Multi-table query - qualify as needed
                        self._auto_qualify_column(ctx, possible_tables, referenced_tables, errors)
                else:
                    # Column is already qualified - validate it
                    self._validate_qualified_column(ctx, table_aliases, errors)
    
    def _auto_qualify_column(
        self, 
        ctx: dict, 
        possible_tables: List[str], 
        referenced_tables: Set[str],
        errors: List[str]
    ):
        """Auto-qualify unqualified column in multi-table query"""
        col_name = ctx['node'].name
        
        if len(possible_tables) == 1:
            target_table = possible_tables[0]
            if target_table in referenced_tables:
                ctx['node'].set('table', target_table)
                errors.append(f"Auto-qualified '{col_name}' as '{target_table}.{col_name}'")
            else:
                errors.append(
                    f"ERROR: Column '{col_name}' from table '{target_table}' "
                    f"used but table not in FROM/JOIN"
                )
                ctx['node'].set('table', target_table)
        
        elif len(possible_tables) > 1:
            available = [t for t in possible_tables if t in referenced_tables]
            
            if len(available) == 1:
                ctx['node'].set('table', available[0])
                errors.append(f"Disambiguated '{col_name}' to '{available[0]}.{col_name}'")
            elif len(available) == 0:
                errors.append(
                    f"ERROR: Ambiguous column '{col_name}' - "
                    f"exists in {possible_tables} but none are in query"
                )
                ctx['node'].set('table', possible_tables[0])
            else:
                errors.append(f"ERROR: Ambiguous column '{col_name}' - could be from {available}")
                ctx['node'].set('table', available[0])
    
    def _validate_qualified_column(
        self, 
        ctx: dict, 
        table_aliases: Dict[str, str],
        errors: List[str]
    ):
        """Validate already qualified column"""
        table = ctx['table']
        col_name = ctx['node'].name
        
        if table in table_aliases.values():
            # Using real table name
            if not self._column_exists_in_table(table, col_name):
                correct_name = self._get_correct_column_name(table, col_name)
                if correct_name != col_name:
                    errors.append(f"Fixed column case in '{table}.{col_name}' -> '{table}.{correct_name}'")
                    ctx['node'].set('name', correct_name)
                else:
                    errors.append(f"ERROR: Column '{col_name}' does not exist in table '{table}'")
        elif table in table_aliases:
            # Using alias
            real_table = table_aliases[table]
            if not self._column_exists_in_table(real_table, col_name):
                correct_name = self._get_correct_column_name(real_table, col_name)
                if correct_name != col_name:
                    errors.append(f"Fixed column case in '{table}.{col_name}' -> '{table}.{correct_name}'")
                    ctx['node'].set('name', correct_name)
                else:
                    errors.append(
                        f"ERROR: Column '{col_name}' does not exist in table '{table}' "
                        f"(alias for '{real_table}')"
                    )
        else:
            # Unknown table reference
            if table not in self.schema_tables:
                errors.append(f"ERROR: Table '{table}' in '{table}.{col_name}' not in schema")
    
    def _post_process_sql(self, sql: str) -> str:
        """Clean up generated SQL"""
        # Remove unnecessary subqueries
        sql = re.sub(
            r'WHERE\s+(\w+)\s*=\s*\(SELECT\s+\1\s+FROM\s+\w+\)',
            '',
            sql,
            flags=re.IGNORECASE
        )
        
        # Clean up extra whitespace
        sql = re.sub(r'\s+', ' ', sql).strip()
        
        return sql
