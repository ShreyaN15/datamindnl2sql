"""Simple linter to enforce forbidden import rules from Developer Guidelines.

It fails (exit code != 0) if it finds forbidden patterns like:
 - engine -> engine imports
 - engine -> api imports
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

forbidden = [
    "from app.engines",
    "import app.engines",
    "from app.api",
    "import app.api",
]

issues = []
for p in ROOT.rglob("*.py"):
    # skip virtualenv and tests directory
    if "site-packages" in str(p) or ".venv" in str(p) or "/.venv/" in str(p):
        continue
    text = p.read_text(encoding="utf-8")
    for f in forbidden:
        if f in text and ("app/engines" in str(p) or "app/core" in str(p)):
            issues.append(f"{p}: contains forbidden import pattern '{f}'")

if issues:
    print("Forbidden import rule violations:")
    for i in issues:
        print(i)
    sys.exit(2)
else:
    print("No forbidden import violations found.")
    sys.exit(0)
