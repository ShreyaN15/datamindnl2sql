"""
Align SQL string literals with the natural language question for candidate ranking.

Used when multiple beam candidates are valid; avoids picking SQL whose filter
literals never appeared in the user's wording (common with similar tokens,
e.g. Fiction vs Fantasy).
"""

import re

# SQL string literals that are often valid without appearing verbatim in NL.
_LITERAL_ALIGNMENT_SKIP = frozenset(
    {
        "active",
        "returned",
        "inactive",
        "pending",
        "completed",
        "cancelled",
        "canceled",
        "yes",
        "no",
        "true",
        "false",
        "null",
    }
)


def score_literal_alignment_with_question(question: str, sql: str) -> int:
    """
    Score how well quoted literals in SQL align with the natural language question.

    Returns a small integer suitable for adding to beam-candidate selection score.
    """
    if not question or not sql:
        return 0
    q = question.lower()
    score = 0
    for m in re.finditer(r"'([^']*)'", sql):
        lit = m.group(1).strip()
        if len(lit) < 2:
            continue
        if not re.search(r"[a-zA-Z]", lit):
            continue
        low = lit.lower()
        if low in _LITERAL_ALIGNMENT_SKIP:
            continue
        if low in q or lit in question:
            score += 70
        elif len(lit) >= 3 and re.fullmatch(r"[A-Za-z][A-Za-z\s'-]*", lit):
            score -= 50
    return score
