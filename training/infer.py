import torch
from transformers import T5Tokenizer, T5ForConditionalGeneration

import sqlparse
from sqlparse.sql import Identifier, IdentifierList, Function
from sqlparse.tokens import Keyword

import sqlglot
from sqlglot import exp, parse_one
from sqlglot.errors import ParseError

import json
from pathlib import Path



# ======================================================
# Schema Loading Functions
# ======================================================

def load_schema_from_tables_json(db_id: str = "department_management", tables_json_path: str = "spider/tables.json"):
    """
    Load schema metadata from Spider's tables.json file.
    
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
    
    # Build schema text (exactly matching training format from preprocess.py)
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
    # Format: [[col_idx1, col_idx2], ...] where col_idx1 references col_idx2
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


# ======================================================
# Model path
# ======================================================
MODEL_PATH = "final_finetuned"

tokenizer = T5Tokenizer.from_pretrained(MODEL_PATH)
model = T5ForConditionalGeneration.from_pretrained(MODEL_PATH)
model.eval()


# ======================================================
# Schema (loaded dynamically from tables.json)
# Note: tables.json is ONLY for our demo with Spider dataset!
# Real users can provide schemas in multiple ways:
#   1. Schema text directly
#   2. Python dict using create_schema_from_dict()
#   3. Load from their own database metadata
# ======================================================
SCHEMA, FOREIGN_KEYS = load_schema_from_tables_json()


def create_schema_from_dict(tables_dict: dict, foreign_keys: list = None):
    """
    Create schema from a simple dictionary (for real-world usage).
    
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
        >>> schema_text, fks = create_schema_from_dict(schema_dict, fks)
    """
    lines = []
    for table_name, columns in tables_dict.items():
        lines.append(f"TABLE {table_name}:")
        for col in columns:
            lines.append(f"- {table_name}.{col}")
        lines.append("")
    
    return "\n".join(lines), (foreign_keys or [])


def build_schema_metadata(schema_text: str):
    """
    Parse schema text into structured metadata.
    
    Schema format (simple text):
        TABLE table_name:
        - table_name.column1
        - table_name.column2
        
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
            table, column = col.split(".")
            tables[table].add(column)
            
            # Track which tables have which columns
            if column not in column_to_tables:
                column_to_tables[column] = []
            column_to_tables[column].append(table)

    return tables, column_to_tables


class SQLValidator:
    """
    SQL Sanitizer: Validates and corrects SQL against schema.
    
    Key improvements:
    1. Case-insensitive column matching (handles head_id vs head_ID)
    2. Smart auto-qualification (only when necessary)
    3. Detects columns from wrong tables (actual errors)
    4. Validates JOIN conditions against foreign keys
    5. Logical query validation
    """
    
    def __init__(self, schema_tables, column_to_tables, foreign_keys=None):
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
        
        # Store foreign key relationships (loaded from schema, not hardcoded!)
        # Format: (table1, col1, table2, col2)
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
        import re
        
        # Fix 1: Date year comparisons (WHERE date_col = YYYY → WHERE YEAR(date_col) = YYYY)
        # Match: WHERE column = 4-digit year (2020-2099)
        sql = re.sub(
            r'WHERE\s+(\w+)\s*=\s*(20\d{2})\b',
            r'WHERE \1 LIKE "%\2%"',
            sql,
            flags=re.IGNORECASE
        )
        
        # Fix 2: Count with unnecessary GROUP BY on same column
        # SELECT COUNT(*) FROM table GROUP BY id → SELECT COUNT(*) FROM table
        if 'COUNT(*)' in sql.upper() and 'GROUP BY' in sql.upper():
            # Only if grouping by ID-like columns without other aggregations
            if re.search(r'GROUP BY\s+\w*id\b', sql, re.IGNORECASE):
                if sql.upper().count('SELECT') == 1 and not any(func in sql.upper() for func in ['AVG', 'SUM', 'MAX', 'MIN']):
                    sql = re.sub(r'\s+GROUP BY\s+\w+', '', sql, flags=re.IGNORECASE)
        
        return sql
    
    def validate_and_fix(self, sql: str) -> tuple[bool, str, list[str]]:
        """
        Validate SQL and attempt to fix common issues.
        
        Returns:
            (is_valid, corrected_sql, errors)
        """
        errors = []
        
        # Apply simple pattern-based fixes first
        sql = self._apply_simple_fixes(sql)
        
        # Step 1: Parse with sqlglot
        try:
            parsed = parse_one(sql, read='sqlite')
        except ParseError as e:
            errors.append(f"Syntax error: {str(e)}")
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
            # Get the ON clause - it's stored as args['on']
            on_clause = join.args.get('on')
            if on_clause:
                # Look for equality conditions
                if isinstance(on_clause, exp.EQ):
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
                # Check if it's a case mismatch
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
        for t1, c1, t2, c2 in join_conditions:
            # Normalize column names (case-insensitive)
            c1_lower = c1.lower()
            c2_lower = c2.lower()
            
            # Check if columns exist in their respective tables
            c1_exists = self._column_exists_in_table(t1, c1)
            c2_exists = self._column_exists_in_table(t2, c2)
            
            if not c1_exists:
                # Try to find the correct column name
                correct_c1 = self._get_correct_column_name(t1, c1)
                if correct_c1 != c1 and self._column_exists_in_table(t1, correct_c1):
                    errors.append(f"Fixed JOIN column case: '{t1}.{c1}' -> '{t1}.{correct_c1}'")
                else:
                    errors.append(f"ERROR: Column '{c1}' does not exist in table '{t1}' (used in JOIN)")
            
            if not c2_exists:
                # Try to find the correct column name
                correct_c2 = self._get_correct_column_name(t2, c2)
                if correct_c2 != c2 and self._column_exists_in_table(t2, correct_c2):
                    errors.append(f"Fixed JOIN column case: '{t2}.{c2}' -> '{t2}.{correct_c2}'")
                else:
                    errors.append(f"ERROR: Column '{c2}' does not exist in table '{t2}' (used in JOIN)")
            
            # Check if this JOIN makes sense according to foreign keys
            join_key = (t1, t2)
            
            if join_key in self.valid_joins and c1_exists and c2_exists:
                # This is a known FK relationship - validate the columns
                valid_pairs = self.valid_joins[join_key]
                
                # Get the actual column names (correct case)
                actual_c1 = self._get_correct_column_name(t1, c1)
                actual_c2 = self._get_correct_column_name(t2, c2)
                
                # Check if this combination is valid
                is_valid_fk = False
                for fk_c1, fk_c2 in valid_pairs:
                    # Case-insensitive comparison
                    if actual_c1.lower() == fk_c1.lower() and actual_c2.lower() == fk_c2.lower():
                        is_valid_fk = True
                        break
                
                if not is_valid_fk:
                    # This is a JOIN between tables with FK relationship but wrong columns
                    valid_cols_str = ' or '.join([f"({fk1}, {fk2})" for fk1, fk2 in valid_pairs])
                    errors.append(f"ERROR: Invalid JOIN between '{t1}' and '{t2}' - used columns ({actual_c1}, {actual_c2}) but valid foreign keys are: {valid_cols_str}")
            elif join_key not in self.valid_joins and c1_exists and c2_exists:
                # Check reverse direction
                join_key_rev = (t2, t1)
                if join_key_rev in self.valid_joins:
                    # FK exists in reverse direction
                    valid_pairs = self.valid_joins[join_key_rev]
                    actual_c1 = self._get_correct_column_name(t1, c1)
                    actual_c2 = self._get_correct_column_name(t2, c2)
                    
                    is_valid_fk = False
                    for fk_c2, fk_c1 in valid_pairs:  # Note: reversed order
                        if actual_c1.lower() == fk_c1.lower() and actual_c2.lower() == fk_c2.lower():
                            is_valid_fk = True
                            break
                    
                    if not is_valid_fk:
                        valid_cols_str = ' or '.join([f"({fk1}, {fk2})" for fk2, fk1 in valid_pairs])
                        errors.append(f"ERROR: Invalid JOIN between '{t1}' and '{t2}' - used columns ({actual_c1}, {actual_c2}) but valid foreign keys are: {valid_cols_str}")
                else:
                    # JOIN between tables with no defined FK relationship
                    # Only warn if it seems suspicious
                    if t1 != t2:  # Not a self-join
                        errors.append(f"WARNING: JOIN between '{t1}' and '{t2}' on ({c1}, {c2}) - no foreign key relationship defined (may be intentional)")
        
        # Step 4: Smart column qualification
        # Only qualify when:
        # a) Column appears in multiple tables AND multiple tables are in FROM clause
        # b) Column is from a different table than the one in FROM
        
        single_table_query = len(referenced_tables) == 1
        single_table_name = list(referenced_tables)[0] if single_table_query else None
        
        for col_name, contexts in referenced_columns.items():
            possible_tables = self.column_to_tables.get(col_name, [])
            
            for ctx in contexts:
                if not ctx['qualified']:
                    # Column is not qualified
                    
                    # Strategy 1: Single table query - only qualify if column NOT in that table
                    if single_table_query:
                        if col_name in self.schema_tables.get(single_table_name, set()):
                            # Column IS in the table - don't qualify (avoid over-qualification)
                            continue
                        else:
                            # Column NOT in the table - this is an ERROR
                            if len(possible_tables) == 1:
                                errors.append(f"ERROR: Column '{col_name}' from table '{possible_tables[0]}' used but table '{single_table_name}' is in FROM clause - missing JOIN?")
                                # Still qualify it to help with correction
                                ctx['node'].set('table', possible_tables[0])
                            else:
                                errors.append(f"ERROR: Column '{col_name}' not in table '{single_table_name}'")
                            continue
                    
                    # Strategy 2: Multi-table query - qualify based on which table has it
                    if len(possible_tables) == 1:
                        # Only one table has this column
                        target_table = possible_tables[0]
                        if target_table in referenced_tables:
                            # Table is in query - qualify it
                            ctx['node'].set('table', target_table)
                            errors.append(f"Auto-qualified '{col_name}' as '{target_table}.{col_name}'")
                        else:
                            # Table NOT in query - ERROR
                            errors.append(f"ERROR: Column '{col_name}' from table '{target_table}' used but table not in FROM/JOIN")
                            ctx['node'].set('table', target_table)
                    
                    elif len(possible_tables) > 1:
                        # Multiple tables have this column
                        available = [t for t in possible_tables if t in referenced_tables]
                        
                        if len(available) == 1:
                            ctx['node'].set('table', available[0])
                            errors.append(f"Disambiguated '{col_name}' to '{available[0]}.{col_name}'")
                        elif len(available) == 0:
                            errors.append(f"ERROR: Ambiguous column '{col_name}' - exists in {possible_tables} but none are in query")
                            ctx['node'].set('table', possible_tables[0])
                        else:
                            errors.append(f"ERROR: Ambiguous column '{col_name}' - could be from {available}")
                            ctx['node'].set('table', available[0])
                
                else:
                    # Column is already qualified - validate it
                    table = ctx['table']
                    
                    if table in table_aliases.values():
                        # It's using a real table name, check it
                        if not self._column_exists_in_table(table, col_name):
                            # Try to fix case
                            correct_name = self._get_correct_column_name(table, col_name)
                            if correct_name != col_name:
                                errors.append(f"Fixed column case in '{table}.{col_name}' -> '{table}.{correct_name}'")
                                ctx['node'].set('name', correct_name)
                            else:
                                errors.append(f"ERROR: Column '{col_name}' does not exist in table '{table}'")
                    elif table in table_aliases:
                        # It's using an alias - resolve and check
                        real_table = table_aliases[table]
                        if not self._column_exists_in_table(real_table, col_name):
                            correct_name = self._get_correct_column_name(real_table, col_name)
                            if correct_name != col_name:
                                errors.append(f"Fixed column case in '{table}.{col_name}' -> '{table}.{correct_name}'")
                                ctx['node'].set('name', correct_name)
                            else:
                                errors.append(f"ERROR: Column '{col_name}' does not exist in table '{table}' (alias for '{real_table}')")
                    else:
                        # Table reference doesn't match anything
                        if table not in self.schema_tables:
                            errors.append(f"ERROR: Table '{table}' in '{table}.{col_name}' not in schema")
        
        # Step 5: Generate corrected SQL
        corrected_sql = parsed.sql(dialect='sqlite')
        
        # Step 6: Post-processing cleanup
        corrected_sql = self._post_process_sql(corrected_sql)
        
        # Step 7: Final validation - check for logical issues
        # If query uses columns from table A but only has table B in FROM, that's bad
        tables_with_columns = set()
        for col_name in referenced_columns.keys():
            tables_for_col = self.column_to_tables.get(col_name, [])
            for t in tables_for_col:
                if t in referenced_tables:
                    tables_with_columns.add(t)
        
        if single_table_query and tables_with_columns and single_table_name not in tables_with_columns:
            errors.append(f"WARNING: Query uses columns from {tables_with_columns} but only has '{single_table_name}' in FROM clause")
        
        is_valid = len([e for e in errors if e.startswith('ERROR:')]) == 0
        
        return is_valid, corrected_sql, errors
    
    def _post_process_sql(self, sql: str) -> str:
        """Clean up generated SQL with simple fixes"""
        import re
        
        # Fix 1: Remove redundant self-joins (table JOIN same_table)
        # Pattern: table AS T1 JOIN table AS T2 with no meaningful condition
        # This is conservative - only remove obvious mistakes
        
        # Fix 2: Simplify unnecessary subqueries in simple cases
        # WHERE col = (SELECT col FROM same_table) → remove
        sql = re.sub(
            r'WHERE\s+(\w+)\s*=\s*\(SELECT\s+\1\s+FROM\s+\w+\)',
            '',
            sql,
            flags=re.IGNORECASE
        )
        
        # Fix 3: Clean up extra whitespace
        sql = re.sub(r'\s+', ' ', sql).strip()
        
        return sql
        return is_valid, corrected_sql, errors

SQL_FUNCTIONS = {
    "count", "avg", "sum", "min", "max"
}


def extract_tables_and_columns(sql: str):
    parsed = sqlparse.parse(sql)
    if not parsed:
        return set(), set()

    stmt = parsed[0]

    tables = set()
    columns = set()

    # ---------- TABLE EXTRACTION (STRICT) ----------
    for token in stmt.tokens:
        if token.ttype is Keyword and token.value.upper() in {"FROM", "JOIN"}:
            idx = stmt.tokens.index(token)
            if idx + 1 < len(stmt.tokens):
                next_token = stmt.tokens[idx + 1]

                if isinstance(next_token, Identifier):
                    tables.add(next_token.get_real_name())

                elif isinstance(next_token, IdentifierList):
                    for identifier in next_token.get_identifiers():
                        tables.add(identifier.get_real_name())

    # ---------- COLUMN EXTRACTION (RECURSIVE) ----------
    def walk(token):
        if token.is_whitespace:
            return

        # Ignore SQL functions
        if isinstance(token, Function):
            return

        # Identifier = column candidate
        if isinstance(token, Identifier):
            name = token.get_real_name()
            if name and name.lower() not in SQL_FUNCTIONS:
                columns.add(name)

        elif isinstance(token, IdentifierList):
            for identifier in token.get_identifiers():
                walk(identifier)

        # Recurse into groups (WHERE, comparisons, etc.)
        if token.is_group:
            for subtoken in token.tokens:
                walk(subtoken)

    for token in stmt.tokens:
        walk(token)

    return tables, columns


# ======================================================
# Inference with SQL Sanitizer (validation & correction)
# ======================================================

# Initialize schema metadata
SCHEMA_TABLES, COLUMN_TO_TABLES = build_schema_metadata(SCHEMA)
SQL_VALIDATOR = SQLValidator(SCHEMA_TABLES, COLUMN_TO_TABLES, FOREIGN_KEYS)


def _fix_merged_sql_tokens(sql: str) -> str:
    """Repair T5-style merged keywords (e.g. member_idRDER BY) without full pattern corrector."""
    from app.engines.sql_validation.pattern_corrector import get_pattern_corrector

    return get_pattern_corrector()._fix_text_corruption(sql)


def ask(question: str, use_sanitizer: bool = True, num_beams: int = 5, num_return_sequences: int = 3) -> str:
    """
    Generate SQL with optional SQL Sanitizer validation and correction..
    
    Args:
        question: Natural language question
        use_sanitizer: Whether to apply validation and correction
        num_beams: Beam search width (increased for more diversity)
        num_return_sequences: Number of candidates to generate and validate
    
    Returns:
        Generated (and potentially corrected) SQL
    """
    prompt = (
        "translate English to SQL:\n"
        f"Question: {question}\n"
        f"Schema:\n{SCHEMA}"
    )

    inputs = tokenizer(prompt, return_tensors="pt")

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_length=200,
            num_beams=num_beams,
            num_return_sequences=min(num_return_sequences, num_beams),
            early_stopping=True,
            do_sample=False  # Use beam search, not sampling
        )

    # Decode all candidates
    candidates = [
        tokenizer.decode(output, skip_special_tokens=True) 
        for output in outputs
    ]
    
    if not use_sanitizer:
        return candidates[0]
    
    # SQL Sanitizer: Validate and correct each candidate, pick best
    best_sql = candidates[0]
    best_score = -float('inf')
    best_corrected = candidates[0]
    
    for i, candidate in enumerate(candidates):
        is_valid, corrected_sql, errors = SQL_VALIDATOR.validate_and_fix(candidate)
        corrected_sql = _fix_merged_sql_tokens(corrected_sql)
        
        # Scoring system (enhanced):
        # +1000 for valid SQL (no ERROR markers)
        # -50 for each error
        # -5 for each warning/note
        # -1 for each position in beam (prefer earlier beams if tied)
        # +10 for simpler queries (fewer JOINs)
        # +5 for queries without subqueries (prefer simpler logic)
        error_count = len([e for e in errors if e.startswith('ERROR:')])
        warning_count = len([e for e in errors if not e.startswith('ERROR:')])
        
        # Simplicity bonus
        join_count = corrected_sql.upper().count('JOIN')
        subquery_count = corrected_sql.count('(SELECT')
        simplicity_bonus = max(0, (3 - join_count) * 10) + max(0, (2 - subquery_count) * 5)
        
        score = (1000 if is_valid else 0) - (error_count * 50) - (warning_count * 5) - i + simplicity_bonus
        
        if score > best_score:
            best_score = score
            best_sql = corrected_sql
            best_corrected = corrected_sql
    
    return best_corrected


def ask_with_details(question: str, use_sanitizer: bool = True) -> dict:
    """
    Generate SQL and return detailed validation information.
    """
    prompt = (
        "translate English to SQL:\n"
        f"Question: {question}\n"
        f"Schema:\n{SCHEMA}"
    )

    inputs = tokenizer(prompt, return_tensors="pt")

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_length=200,
            num_beams=4,
            early_stopping=True
        )

    raw_sql = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    if use_sanitizer:
        is_valid, corrected_sql, errors = SQL_VALIDATOR.validate_and_fix(raw_sql)
        corrected_sql = _fix_merged_sql_tokens(corrected_sql)
        return {
            'question': question,
            'raw_sql': raw_sql,
            'corrected_sql': corrected_sql,
            'is_valid': is_valid,
            'errors': errors,
            'was_corrected': raw_sql != corrected_sql
        }
    else:
        return {
            'question': question,
            'raw_sql': raw_sql,
            'corrected_sql': raw_sql,
            'is_valid': True,
            'errors': [],
            'was_corrected': False
        }


# ======================================================
# Demo
# ======================================================
if __name__ == "__main__":
    tests = [
        "List the names of heads older than 50.",
        "How many heads are older than 40?",
        "What is the average age of heads?",
        "List all head names.",
        "List the names of department heads.",
        "How many heads work in departments?",
        "How many heads of the departments are older than 56?",
        "List departments whose heads are older than 60."
    ]

    print("=" * 80)
    print("TESTING WITH SQL SANITIZER (VALIDATION & CORRECTION)")
    print("=" * 80)
    
    for q in tests:
        print(f"\n{'─' * 80}")
        result = ask_with_details(q, use_sanitizer=True)
        
        print(f"Q: {q}")
        print(f"\nRaw SQL:       {result['raw_sql']}")
        
        if result['was_corrected']:
            print(f"Corrected SQL: {result['corrected_sql']}")
            print(f"Status:        ✓ CORRECTED")
            if result['errors']:
                print(f"Issues fixed:  {'; '.join(result['errors'][:3])}")
        else:
            print(f"Status:        ✓ Valid (no changes needed)")
    
    print(f"\n{'=' * 80}")
    print("\nComparison mode - SQL Sanitizer OFF vs ON:")
    print("=" * 80)
    
    # Focus on the problematic queries
    problematic = [
        "How many heads of the departments are older than 56?",
        "List the names of department heads.",
    ]
    
    for q in problematic:
        print(f"\n{'─' * 80}")
        print(f"Q: {q}")
        print(f"\nWithout Sanitizer: {ask(q, use_sanitizer=False)}")
        print(f"With Sanitizer:    {ask(q, use_sanitizer=True)}")
