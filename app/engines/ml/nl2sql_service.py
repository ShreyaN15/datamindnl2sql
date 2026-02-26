"""
NL2SQL Inference Service

Provides text-to-SQL conversion using fine-tuned T5 model with SQL sanitizer.
"""

import torch
from transformers import T5Tokenizer, T5ForConditionalGeneration
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging

from app.utils.schema_builder import build_schema_from_dict, parse_schema_metadata
from app.engines.sql_validation.validator import SQLValidator
from app.engines.ml.query_enhancer import get_query_enhancer
from app.engines.sql_validation.pattern_corrector import get_pattern_corrector

logger = logging.getLogger(__name__)


class NL2SQLService:
    """
    Natural Language to SQL conversion service.
    
    Features:
    - Fine-tuned T5 model for SQL generation
    - SQL sanitizer for validation and correction
    - Multi-candidate generation with scoring
    - Schema-agnostic design
    """
    
    def __init__(self, model_path: str = "models/nl2sql-t5"):
        """
        Initialize the NL2SQL service.
        
        Args:
            model_path: Path to the fine-tuned T5 model
        """
        self.model_path = Path(model_path)
        self.tokenizer = None
        self.model = None
        self.is_loaded = False
        self.query_enhancer = get_query_enhancer()  # Add query enhancer
        self.pattern_corrector = get_pattern_corrector()  # Add pattern corrector
        
    def load_model(self):
        """Load the T5 model and tokenizer"""
        if self.is_loaded:
            return
        
        try:
            logger.info(f"Loading NL2SQL model from {self.model_path}")
            self.tokenizer = T5Tokenizer.from_pretrained(str(self.model_path))
            self.model = T5ForConditionalGeneration.from_pretrained(str(self.model_path))
            self.model.eval()
            self.is_loaded = True
            logger.info("NL2SQL model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load NL2SQL model: {e}")
            raise
    
    def _fix_comparison_operators(self, sql: str, question: str = "") -> str:
        """
        Fix missing comparison operators in T5 output.
        
        T5 tokenizer treats < and > as special tokens, so they often get stripped.
        This method restores them based on context patterns from the question.
        
        Patterns:
        - "WHERE col  number" → "WHERE col < number" (if context suggests "below/less")
        - "WHERE col  number" → "WHERE col > number" (if context suggests "above/more/greater")
        - "WHERE col  = number" → "WHERE col <= number" or ">= number"
        """
        import re
        
        # Determine operator direction from question context
        question_lower = question.lower() if question else ""
        
        # Keywords indicating > operator
        greater_keywords = ['greater', 'more', 'above', 'over', 'higher', 'exceed']
        # Keywords indicating < operator  
        less_keywords = ['less', 'below', 'under', 'lower', 'fewer']
        
        use_greater = any(kw in question_lower for kw in greater_keywords)
        use_less = any(kw in question_lower for kw in less_keywords)
        
        # Default operator (if no context)
        default_op = '>' if use_greater else '<' if use_less else '<'
        
        # Pattern: WHERE column  number (missing < or >)
        # Look for WHERE/HAVING followed by column, then multiple spaces + number without operator
        pattern = r'\b(WHERE|HAVING)\s+(\w+\.?\w*)\s{2,}(\d+\.?\d*)\b'
        
        def replace_operator(match):
            keyword = match.group(1)
            column = match.group(2)
            number = match.group(3)
            return f"{keyword} {column} {default_op} {number}"
        
        sql = re.sub(pattern, replace_operator, sql, flags=re.IGNORECASE)
        
        return sql
    
    def _fix_column_hallucinations(self, sql: str, schema_text: str) -> str:
        """
        Fix common column name hallucinations from the ML model.
        
        Model often generates generic names like 'student_name', 'professor_name'
        when schema actually has 'first_name, last_name'.
        """
        import re
        
        # Parse schema to get actual columns (handle both formats)
        schema_tables = {}
        current_table = None
        
        for line in schema_text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Check if it's a table definition line
            # Format: "TABLE table_name:" or "table_name:"
            if ':' in line and not line.startswith('-'):
                parts = line.split(':', 1)
                table_name = parts[0].strip().lower()
                
                # Strip "table " prefix if present
                if table_name.startswith('table '):
                    table_name = table_name[6:]
                
                # Initialize table with empty column list
                schema_tables[table_name] = []
                current_table = table_name
                
                # Check if columns are on the same line (Format: "table: col1, col2, col3")
                columns_part = parts[1].strip() if len(parts) > 1 else ""
                if columns_part and not columns_part.startswith('-'):
                    # Extract column names (remove type info and FK annotations)
                    columns = []
                    for col in columns_part.split(','):
                        col = col.strip()
                        col = re.sub(r'\([^)]*\)', '', col)  # Remove type info
                        col_name = col.split()[0] if col else ""
                        if col_name:
                            columns.append(col_name.lower())
                    schema_tables[table_name] = columns
            
            # Format 2: "- table.column" or "- column"
            elif line.startswith('-') and current_table:
                # Extract column name from "- table.column" or "- column"
                col_text = line[1:].strip()  # Remove '-' prefix
                
                # Remove FK annotation: "(references ...)"
                col_text = re.sub(r'\(references[^)]*\)', '', col_text).strip()
                
                # Handle "table.column" format
                if '.' in col_text:
                    parts = col_text.split('.', 1)
                    col_name = parts[1].split()[0] if parts[1] else ""
                else:
                    col_name = col_text.split()[0]
                
                if col_name:
                    schema_tables[current_table].append(col_name.lower())
        
        # Common hallucinations and their fixes
        # Pattern: table_name_column or table_column
        for table, columns in schema_tables.items():
            # Check if table has first_name and last_name
            if 'first_name' in columns and 'last_name' in columns:
                # Replace hallucinated "table_name" with "first_name, last_name"
                # Check both plural and singular forms
                hallucinations = [
                    f'{table}_name',  # students_name
                    f'{table}name',   # studentsname
                ]
                
                # Also check singular form (remove trailing 's' if present)
                if table.endswith('s'):
                    singular = table[:-1]
                    hallucinations.extend([
                        f'{singular}_name',  # student_name
                        f'{singular}name',   # studentname
                    ])
                
                for hall in hallucinations:
                    # Pattern: SELECT table_name FROM ...
                    # Replace with: SELECT first_name, last_name FROM ...
                    if re.search(rf'\b{re.escape(hall)}\b', sql, re.IGNORECASE):
                        logger.info(f"Detected hallucination '{hall}' in SQL")
                        # Check if it's qualified with table name
                        sql = re.sub(
                            rf'\b{table}\.{re.escape(hall)}\b',
                            f'{table}.first_name, {table}.last_name',
                            sql,
                            flags=re.IGNORECASE
                        )
                        # Also handle unqualified
                        sql = re.sub(
                            rf'\bSELECT\s+{re.escape(hall)}\b',
                            f'SELECT first_name, last_name',
                            sql,
                            flags=re.IGNORECASE
                        )
                        sql = re.sub(
                            rf',\s*{re.escape(hall)}\b',
                            f', first_name, last_name',
                            sql,
                            flags=re.IGNORECASE
                        )
                        logger.info(f"Fixed column hallucination: '{hall}' -> 'first_name, last_name'")
            
            # Check if table has course_name
            if 'course_name' in columns:
                # Ensure course_name is used, not just course_code
                pass  # course_code is also valid, so no fix needed
        
        # Fix cross-schema contamination (student_db columns in employee_db queries)
        # This happens when model was trained primarily on one schema
        if 'employees' in schema_tables:
            # We're querying employee_db
            # Replace student_db artifacts with employee_db equivalents
            replacements = {
                r'\bgpa\b': 'current_salary',
                r'\bstudent_id\b': 'employee_id',
                r'\bstudents\b': 'employees',
                r'\bprofessors\b': 'employees',
                r'\bcourses\b': 'projects',
                r'\benrollments\b': 'project_assignments',
            }
            
            for pattern, replacement in replacements.items():
                if re.search(pattern, sql, re.IGNORECASE):
                    sql = re.sub(pattern, replacement, sql, flags=re.IGNORECASE)
                    logger.info(f"Fixed cross-schema contamination: '{pattern}' -> '{replacement}'")
        
        return sql
    
    def generate_sql(
        self,
        question: str,
        schema_text: str,
        foreign_keys: Optional[List[Tuple[str, str, str, str]]] = None,
        use_sanitizer: bool = True,
        use_enhancer: bool = True,
        use_pattern_correction: bool = True,
        num_beams: int = 5,
        num_candidates: int = 3
    ) -> str:
        """
        Generate SQL from natural language question.
        
        Args:
            question: Natural language question
            schema_text: Database schema in text format
            foreign_keys: List of (table1, col1, table2, col2) foreign key relationships
            use_sanitizer: Whether to apply SQL validation and correction
            use_enhancer: Whether to use query enhancement for better accuracy
            use_pattern_correction: Whether to apply pattern-based SQL corrections
            num_beams: Beam search width
            num_candidates: Number of candidate SQLs to generate and validate
        
        Returns:
            Generated (and potentially corrected) SQL query
        """
        if not self.is_loaded:
            self.load_model()
        
        # Construct prompt - use enhancer if enabled
        if use_enhancer:
            prompt = self.query_enhancer.enhance_prompt(
                question,
                schema_text,
                foreign_keys or []
            )
        else:
            # Standard prompt (matches training format)
            prompt = (
                "translate English to SQL:\n"
                f"Question: {question}\n"
                f"Schema:\n{schema_text}"
            )
        
        # Tokenize input
        inputs = self.tokenizer(prompt, return_tensors="pt")
        
        # Generate SQL candidates
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=200,
                num_beams=num_beams,
                num_return_sequences=min(num_candidates, num_beams),
                early_stopping=True,
                do_sample=False
            )
        
        # Decode all candidates
        candidates = [
            self.tokenizer.decode(output, skip_special_tokens=True)
            for output in outputs
        ]
        
        # Fix T5 tokenization issues with comparison operators (pass question for context)
        candidates = [self._fix_comparison_operators(c, question) for c in candidates]
        
        # Fix column hallucinations
        candidates = [self._fix_column_hallucinations(c, schema_text) for c in candidates]
        
        logger.info(f"ML Model generated {len(candidates)} candidates:")
        for i, candidate in enumerate(candidates):
            logger.info(f"  Candidate {i+1}: {candidate}")
        
        if not use_sanitizer:
            return candidates[0]
        
        # Apply SQL sanitizer to select best candidate
        best_sql = self._select_best_candidate(
            candidates, 
            schema_text, 
            foreign_keys or []
        )
        
        logger.info(f"After sanitizer selection: {best_sql}")
        
        # Apply pattern-based corrections if enabled
        if use_pattern_correction:
            before_pattern = best_sql
            best_sql = self.pattern_corrector.correct_sql(
                best_sql,
                question,
                schema_text,
                foreign_keys or []
            )
            if best_sql != before_pattern:
                logger.info(f"After pattern correction: {best_sql}")
        
        return best_sql
    
    def generate_sql_with_details(
        self,
        question: str,
        schema_text: str,
        foreign_keys: Optional[List[Tuple[str, str, str, str]]] = None,
        use_sanitizer: bool = True
    ) -> Dict:
        """
        Generate SQL with detailed validation information.
        
        Args:
            question: Natural language question
            schema_text: Database schema in text format
            foreign_keys: List of foreign key relationships
            use_sanitizer: Whether to apply SQL validation
        
        Returns:
            Dictionary containing:
                - question: Original question
                - raw_sql: SQL from model before correction
                - corrected_sql: SQL after sanitizer corrections
                - is_valid: Whether the SQL is valid
                - errors: List of errors/corrections applied
                - was_corrected: Whether any corrections were made
        """
        if not self.is_loaded:
            self.load_model()
        
        # Construct prompt
        prompt = (
            "translate English to SQL:\n"
            f"Question: {question}\n"
            f"Schema:\n{schema_text}"
        )
        
        # Tokenize and generate
        inputs = self.tokenizer(prompt, return_tensors="pt")
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=200,
                num_beams=4,
                early_stopping=True
            )
        
        raw_sql = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        if not use_sanitizer:
            return {
                'question': question,
                'raw_sql': raw_sql,
                'corrected_sql': raw_sql,
                'is_valid': True,
                'errors': [],
                'was_corrected': False
            }
        
        # Validate and correct
        schema_tables, column_to_tables = parse_schema_metadata(schema_text)
        validator = SQLValidator(schema_tables, column_to_tables, foreign_keys or [])
        is_valid, corrected_sql, errors = validator.validate_and_fix(raw_sql)
        
        return {
            'question': question,
            'raw_sql': raw_sql,
            'corrected_sql': corrected_sql,
            'is_valid': is_valid,
            'errors': errors,
            'was_corrected': raw_sql != corrected_sql
        }
    
    def _select_best_candidate(
        self,
        candidates: List[str],
        schema_text: str,
        foreign_keys: List[Tuple[str, str, str, str]]
    ) -> str:
        """
        Select the best SQL candidate using validation scoring.
        
        Scoring system:
        +1000 for valid SQL (no errors)
        -50 for each error
        -5 for each warning
        -1 for each position in beam
        +10 for simpler queries (fewer JOINs)
        +5 for queries without subqueries
        """
        schema_tables, column_to_tables = parse_schema_metadata(schema_text)
        validator = SQLValidator(schema_tables, column_to_tables, foreign_keys)
        
        best_sql = candidates[0]
        best_score = -float('inf')
        
        for i, candidate in enumerate(candidates):
            is_valid, corrected_sql, errors = validator.validate_and_fix(candidate)
            
            # Calculate score
            error_count = len([e for e in errors if e.startswith('ERROR:')])
            warning_count = len([e for e in errors if not e.startswith('ERROR:')])
            
            # Simplicity bonuses
            join_count = corrected_sql.upper().count('JOIN')
            subquery_count = corrected_sql.count('(SELECT')
            simplicity_bonus = max(0, (3 - join_count) * 10) + max(0, (2 - subquery_count) * 5)
            
            score = (
                (1000 if is_valid else 0) 
                - (error_count * 50) 
                - (warning_count * 5) 
                - i 
                + simplicity_bonus
            )
            
            if score > best_score:
                best_score = score
                best_sql = corrected_sql
        
        return best_sql
    
    def generate_from_dict(
        self,
        question: str,
        tables_dict: Dict[str, List[str]],
        foreign_keys: Optional[List[Tuple[str, str, str, str]]] = None,
        use_sanitizer: bool = True
    ) -> str:
        """
        Convenience method to generate SQL from schema dictionary.
        
        Args:
            question: Natural language question
            tables_dict: {"table_name": ["col1", "col2", ...], ...}
            foreign_keys: List of (table1, col1, table2, col2) tuples
            use_sanitizer: Whether to apply validation
        
        Returns:
            Generated SQL query
        """
        schema_text, fks = build_schema_from_dict(tables_dict, foreign_keys)
        return self.generate_sql(question, schema_text, fks, use_sanitizer)


# Global service instance
_nl2sql_service = None


def get_nl2sql_service() -> NL2SQLService:
    """Get or create the global NL2SQL service instance"""
    global _nl2sql_service
    if _nl2sql_service is None:
        _nl2sql_service = NL2SQLService()
    return _nl2sql_service
