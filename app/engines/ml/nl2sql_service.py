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
    
    def generate_sql(
        self,
        question: str,
        schema_text: str,
        foreign_keys: Optional[List[Tuple[str, str, str, str]]] = None,
        use_sanitizer: bool = True,
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
            num_beams: Beam search width
            num_candidates: Number of candidate SQLs to generate and validate
        
        Returns:
            Generated (and potentially corrected) SQL query
        """
        if not self.is_loaded:
            self.load_model()
        
        # Construct prompt (matches training format)
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
        
        if not use_sanitizer:
            return candidates[0]
        
        # Apply SQL sanitizer to select best candidate
        return self._select_best_candidate(
            candidates, 
            schema_text, 
            foreign_keys or []
        )
    
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
