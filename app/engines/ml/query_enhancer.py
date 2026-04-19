"""
Query Enhancement Module

Improves NL2SQL accuracy by adding contextual hints and examples to the model prompt.
This module specifically targets JOIN accuracy for student/university databases.

Key Features:
- Detects query patterns that require JOINs
- Adds relevant example queries to prompt
- Provides relationship hints based on detected intent
- No model retraining required - works with existing model
"""

import re
from typing import List, Tuple, Optional, Dict
import logging

logger = logging.getLogger(__name__)


class QueryEnhancer:
    """
    Enhances natural language queries with contextual examples and hints
    to improve SQL generation accuracy, especially for JOINs.
    """
    
    def __init__(self):
        # Domain-specific examples for student/university databases
        # Format: (pattern keywords, example NL, example SQL, hint)
        self.domain_examples = [
            # JOIN examples for student database
            {
                'keywords': ['students', 'department', 'major'],
                'nl': 'Show students with their department names',
                'sql': 'SELECT s.first_name, s.last_name, d.department_name FROM students s JOIN departments d ON s.department_id = d.department_id',
                'hint': 'Use JOIN when combining students and departments'
            },
            {
                'keywords': ['courses', 'professor', 'taught', 'teaching'],
                'nl': 'List courses with professor names',
                'sql': 'SELECT c.course_name, p.first_name, p.last_name FROM courses c JOIN professors p ON c.professor_id = p.professor_id',
                'hint': 'Use JOIN to connect courses with professors'
            },
            {
                'keywords': ['students', 'enrolled', 'courses', 'taking'],
                'nl': 'Show students enrolled in each course',
                'sql': 'SELECT s.first_name, s.last_name, c.course_name FROM students s JOIN enrollments e ON s.student_id = e.student_id JOIN courses c ON e.course_id = c.course_id',
                'hint': 'Use enrollments table to connect students and courses'
            },
            {
                'keywords': ['how many', 'count', 'students', 'department', 'each'],
                'nl': 'How many students in each department?',
                'sql': 'SELECT d.department_name, COUNT(s.student_id) FROM departments d LEFT JOIN students s ON d.department_id = s.department_id GROUP BY d.department_name',
                'hint': 'Use LEFT JOIN and GROUP BY for counting per group'
            },
            {
                'keywords': ['average', 'gpa', 'department', 'by'],
                'nl': 'What is the average GPA by department?',
                'sql': 'SELECT d.department_name, AVG(s.gpa) FROM departments d JOIN students s ON d.department_id = s.department_id GROUP BY d.department_name',
                'hint': 'Use JOIN and GROUP BY for aggregations per department'
            },
            {
                'keywords': ['courses', 'professor', 'how many', 'teach'],
                'nl': 'How many courses does each professor teach?',
                'sql': 'SELECT p.first_name, p.last_name, COUNT(c.course_id) FROM professors p LEFT JOIN courses c ON p.professor_id = c.professor_id GROUP BY p.professor_id, p.first_name, p.last_name',
                'hint': 'Use LEFT JOIN and GROUP BY with professor details'
            },
            {
                'keywords': ['students', 'more than', 'courses', 'enrolled'],
                'nl': 'Find students enrolled in more than 2 courses',
                'sql': 'SELECT s.first_name, s.last_name, COUNT(e.course_id) as course_count FROM students s JOIN enrollments e ON s.student_id = e.student_id GROUP BY s.student_id, s.first_name, s.last_name HAVING COUNT(e.course_id) > 2',
                'hint': 'Use JOIN, GROUP BY, and HAVING for filtered counts'
            },
            {
                'keywords': ['grades', 'students', 'scores', 'assignments'],
                'nl': 'Show student grades with student names',
                'sql': 'SELECT s.first_name, s.last_name, g.assignment_name, g.score FROM students s JOIN enrollments e ON s.student_id = e.student_id JOIN grades g ON e.enrollment_id = g.enrollment_id',
                'hint': 'Use enrollments to connect students with grades'
            },
            {
                'keywords': ['courses', 'offered', 'department'],
                'nl': 'List courses offered by the Computer Science department',
                'sql': "SELECT c.course_name, c.course_code FROM courses c JOIN departments d ON c.department_id = d.department_id WHERE d.department_name = 'Computer Science'",
                'hint': 'Join courses to departments on department_id; filter by department_name, not student names',
                # Do not inject this literal-heavy example unless NL names a department or says "offered by"
                # (avoids matching "courses" + "offered" in "offered in Fall 2025" alone).
                'require_any_substrings': ['department'],
                'require_any_regexes': [r'\boffered\s+by\b'],
            },
            {
                'keywords': ['courses', 'offered'],
                'nl': 'List all courses offered in Fall 2025',
                'sql': "SELECT c.course_name, c.course_code FROM courses c WHERE c.semester = 'Fall 2025'",
                'hint': 'When the question gives a term and year (e.g. Fall 2025), filter courses.semester; do not invent a department.',
                'require_any_substrings': ['semester'],
                'require_any_regexes': [
                    r'\b(?:fall|spring|summer|winter)\s+\d{4}\b',
                ],
            },
            {
                'keywords': ['students', 'courses', 'taught'],
                'nl': 'List students taking courses taught by Alan Turing',
                'sql': "SELECT s.first_name, s.last_name, c.course_name FROM students s JOIN enrollments e ON s.student_id = e.student_id JOIN courses c ON e.course_id = c.course_id JOIN professors p ON c.professor_id = p.professor_id WHERE p.first_name = 'Alan' AND p.last_name = 'Turing'",
                'hint': 'Students to courses go through enrollments; filter instructor on professors via courses.professor_id'
            },
            {
                'keywords': ['students', 'enrolled', 'course', 'code'],
                'nl': 'Show all students enrolled in course code CS101',
                'sql': "SELECT s.first_name, s.last_name FROM students s JOIN enrollments e ON s.student_id = e.student_id JOIN courses c ON e.course_id = c.course_id WHERE c.course_code = 'CS101'",
                'hint': 'Use enrollments to link students and courses; filter by course_code when the question gives a code'
            },
        ]
        
        # JOIN trigger patterns - phrases that often require JOINs
        self.join_triggers = [
            r'\balong\s+with\b',
            r'\bwith\s+(their|its|the)\s+\w+\s+(name|detail|info)',
            r'\b(each|every)\s+\w+.*\b(in|from|of)\s+\w+',
            r'\bhow\s+many\s+\w+.*\b(per|for each|in each)',
            r'\baverage\s+\w+.*\bby\s+\w+',
            r'\benrolled\s+in',
            r'\btaught\s+by',
            r'\bbelongs?\s+to',
            r'\bstudents?\s+.*\bdepartment',
            r'\bcourses?\s+.*\bprofessor',
            r'\blist\s+\w+\s+with',
            r'\boffered\s+by\b',
            r'\bcourses?\b.*\bdepartment\b',
            r'\bdepartment\b.*\bcourses?\b',
            r'\bcourse\s+code\b',
            r'\bstudents?\b.*\btaught\s+by\b',
        ]
        
        # Aggregation patterns
        self.aggregation_patterns = [
            r'\bhow\s+many\b',
            r'\bcount\b',
            r'\baverage\b',
            r'\bavg\b',
            r'\bsum\s+of\b',
            r'\btotal\b',
            r'\bmaximum\b',
            r'\bmax\b',
            r'\bminimum\b',
            r'\bmin\b',
        ]
        
        # GROUP BY triggers
        self.groupby_triggers = [
            r'\bper\s+\w+',
            r'\bfor\s+each\s+\w+',
            r'\bin\s+each\s+\w+',
            r'\bby\s+\w+$',
            r'\bgrouped\s+by',
        ]
    
    def enhance_prompt(
        self,
        question: str,
        schema_text: str,
        foreign_keys: List[Tuple[str, str, str, str]]
    ) -> str:
        """
        Enhance the model prompt with contextual examples and hints.
        
        Args:
            question: Original natural language question
            schema_text: Database schema
            foreign_keys: Foreign key relationships
        
        Returns:
            Enhanced prompt string with examples and hints
        """
        question_lower = question.lower()
        
        # Detect query characteristics
        needs_join = self._likely_needs_join(question_lower)
        needs_aggregation = self._likely_needs_aggregation(question_lower)
        needs_groupby = self._likely_needs_groupby(question_lower)
        
        # Find relevant examples
        relevant_examples = self._find_relevant_examples(question_lower, max_examples=2)
        
        # Build enhanced prompt
        prompt_parts = []
        
        # Add examples if found
        if relevant_examples:
            prompt_parts.append("# Example queries:")
            for ex in relevant_examples:
                prompt_parts.append(f"# Q: {ex['nl']}")
                prompt_parts.append(f"# SQL: {ex['sql']}")
                prompt_parts.append("")
        
        # Add relationship hints for JOINs
        if needs_join and foreign_keys:
            prompt_parts.append("# Key relationships:")
            # Group FKs by relevance to question
            relevant_fks = self._get_relevant_foreign_keys(question_lower, foreign_keys)
            for fk in relevant_fks[:3]:  # Top 3 most relevant
                from_table, from_col, to_table, to_col = fk
                prompt_parts.append(f"# {from_table}.{from_col} -> {to_table}.{to_col}")
            prompt_parts.append("")
        
        # Add query type hints
        hints = []
        if needs_join:
            hints.append("Consider using JOIN to combine related tables")
        if needs_aggregation and needs_groupby:
            hints.append("Use GROUP BY with aggregate functions like COUNT, AVG")
        elif needs_aggregation:
            hints.append("Use aggregate function (COUNT, AVG, SUM, MAX, MIN)")
        
        if hints:
            prompt_parts.append("# Hints:")
            for hint in hints:
                prompt_parts.append(f"# {hint}")
            prompt_parts.append("")
        
        # Construct final prompt
        enhanced_prefix = "\n".join(prompt_parts) if prompt_parts else ""
        
        # Standard format (matches training)
        base_prompt = (
            f"translate English to SQL:\n"
            f"Question: {question}\n"
            f"Schema:\n{schema_text}"
        )
        
        if enhanced_prefix:
            return f"{enhanced_prefix}\n{base_prompt}"
        else:
            return base_prompt
    
    def _likely_needs_join(self, question: str) -> bool:
        """Detect if question likely requires JOIN"""
        for pattern in self.join_triggers:
            if re.search(pattern, question, re.IGNORECASE):
                return True
        return False

    def question_suggests_join(self, question: str) -> bool:
        """Public hook for scoring / routing: NL likely needs JOINs."""
        return self._likely_needs_join(question.lower())
    
    def _likely_needs_aggregation(self, question: str) -> bool:
        """Detect if question likely requires aggregation"""
        for pattern in self.aggregation_patterns:
            if re.search(pattern, question, re.IGNORECASE):
                return True
        return False
    
    def _likely_needs_groupby(self, question: str) -> bool:
        """Detect if question likely requires GROUP BY"""
        for pattern in self.groupby_triggers:
            if re.search(pattern, question, re.IGNORECASE):
                return True
        return False
    
    def _find_relevant_examples(self, question: str, max_examples: int = 2) -> List[Dict]:
        """
        Find most relevant example queries based on keyword matching.
        Only returns examples if at least 2 keywords match to ensure relevance.
        
        Args:
            question: Natural language question (lowercase)
            max_examples: Maximum number of examples to return
        
        Returns:
            List of example dictionaries
        """
        scored_examples = []
        
        for example in self.domain_examples:
            # Score based on keyword matches
            score = 0
            for keyword in example['keywords']:
                if keyword in question:
                    score += 1
            
            # Only add if at least 2 keywords match (ensures relevance)
            if score >= 2 and self._example_meets_nl_gates(example, question):
                scored_examples.append((score, example))
        
        # Sort by score (descending) and return top N
        scored_examples.sort(key=lambda x: x[0], reverse=True)
        return [ex for _, ex in scored_examples[:max_examples]]

    def _example_meets_nl_gates(self, example: Dict, question: str) -> bool:
        """
        Optional per-example gates so literal-heavy SQL is not shown unless NL supports it.
        If require_any_substrings or require_any_regexes is set, at least one must match.
        """
        subs = example.get('require_any_substrings') or []
        regexes = example.get('require_any_regexes') or []
        if not subs and not regexes:
            return True
        if any(s in question for s in subs):
            return True
        if any(re.search(rx, question, re.IGNORECASE) for rx in regexes):
            return True
        return False
    
    def _get_relevant_foreign_keys(
        self,
        question: str,
        foreign_keys: List[Tuple[str, str, str, str]]
    ) -> List[Tuple[str, str, str, str]]:
        """
        Filter and rank foreign keys by relevance to the question.
        
        Args:
            question: Natural language question (lowercase)
            foreign_keys: All available foreign keys
        
        Returns:
            Sorted list of relevant foreign keys
        """
        scored_fks = []
        
        for fk in foreign_keys:
            from_table, from_col, to_table, to_col = fk
            score = 0
            
            # Check if table names appear in question
            if from_table.lower() in question or self._singular_form(from_table).lower() in question:
                score += 2
            if to_table.lower() in question or self._singular_form(to_table).lower() in question:
                score += 2
            
            # Bonus for commonly queried relationships
            if 'student' in from_table.lower() or 'student' in to_table.lower():
                if 'student' in question:
                    score += 1
            if 'department' in from_table.lower() or 'department' in to_table.lower():
                if 'department' in question:
                    score += 1
            if 'course' in from_table.lower() or 'course' in to_table.lower():
                if 'course' in question:
                    score += 1
            
            if score > 0:
                scored_fks.append((score, fk))
        
        # Sort by score
        scored_fks.sort(key=lambda x: x[0], reverse=True)
        return [fk for _, fk in scored_fks]
    
    def _singular_form(self, word: str) -> str:
        """Simple singular form (students -> student)"""
        if word.endswith('s') and len(word) > 1:
            return word[:-1]
        return word
    
    def add_custom_example(
        self,
        keywords: List[str],
        nl_question: str,
        sql_query: str,
        hint: str = ""
    ):
        """
        Add a custom example to the enhancer's knowledge base.
        
        Args:
            keywords: Keywords to match against questions
            nl_question: Natural language question
            sql_query: Corresponding SQL query
            hint: Optional hint for this pattern
        """
        self.domain_examples.append({
            'keywords': keywords,
            'nl': nl_question,
            'sql': sql_query,
            'hint': hint
        })
        logger.info(f"Added custom example: {nl_question}")


# Global instance
_query_enhancer = None


def get_query_enhancer() -> QueryEnhancer:
    """Get or create the global query enhancer instance"""
    global _query_enhancer
    if _query_enhancer is None:
        _query_enhancer = QueryEnhancer()
    return _query_enhancer
