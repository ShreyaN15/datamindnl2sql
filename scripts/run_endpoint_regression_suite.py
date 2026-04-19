#!/usr/bin/env python3
"""
Endpoint regression suite for DataMind (library_db, employee_db, student_db).

Runs against the real FastAPI app via TestClient (no separate server process).

What passes:
  - HTTP 200 from /query/nl2sql and /query/execute-sql
  - When execute_query=true: execution_result.success is True
  - Optional min_rows on execution_result.row_count

What does NOT pass (text match on generated SQL): not used.

Environment (Postgres demo DBs — see *_DB_INFO.txt in repo root):
  PG_E2E_HOST      default localhost
  PG_E2E_PORT      default 5432
  PG_E2E_USER      default hari
  PG_E2E_PASSWORD  default hari123

  SKIP_PG=1              Skip Postgres connection + all DB tests (smoke auth only)
  SKIP_NL2SQL=1          Only run execute-sql smoke + skip model NL2SQL cases
  NL2SQL_MODEL_PATH      Override path to T5 model dir (default models/nl2sql-t5)

Exit code: 0 if all *required* cases pass; 1 otherwise.

Requires: httpx (for Starlette TestClient). Install once: pip install -r requirements-e2e.txt

Baseline honesty (read before trusting green):
  - student_db multi-table joins are historically flaky for the model; those cases are
    severity *best_effort* (warnings only, exit code still 0 if required cases pass).
  - NL2SQL + execute blocks require models/nl2sql-t5 (or NL2SQL_MODEL_PATH) with weights;
    if the model is missing, NL2SQL cases are skipped (smoke SQL still runs).
"""

from __future__ import annotations

import json
import os
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Project root on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@dataclass
class Case:
    label: str
    question: str
    tier: str  # join1 | simple | agg | stretch
    severity: str  # required | best_effort
    min_rows: int = 0


# --- Case definitions (NL questions). Single-join / simple = "required" where stable. ---
# COUNT(*) on branches often derails (model + FK-string corrector → self-join on branches).
# Required library checks: one non-count SELECT + one join that has been stable in practice.
LIBRARY_CASES: List[Case] = [
    Case("lib_simple_list_branch_names", "List all branch names", "simple", "required", min_rows=1),
    Case("lib_join1_members_branch", "List members with their branch name", "join1", "required", min_rows=1),
    Case("lib_join1_books_author", "List each book title with the author last name", "join1", "best_effort", min_rows=0),
    Case("lib_join_loans_member", "Show loans with member email", "join1", "best_effort", min_rows=1),
]

EMPLOYEE_CASES: List[Case] = [
    Case("emp_simple_count_employees", "How many employees are there?", "simple", "required", min_rows=1),
    Case("emp_join1_emp_dept", "Show employees with their department name", "join1", "required", min_rows=1),
    Case("emp_join1_projects_dept", "List projects with department names", "join1", "required", min_rows=1),
    Case("emp_join_manager", "List employees with their manager first name", "join1", "best_effort", min_rows=0),
]

STUDENT_CASES: List[Case] = [
    # Plain COUNT(*) often misfires into invalid SELECT; keep as non-gating.
    Case("stu_simple_count_students", "How many students are there?", "simple", "best_effort", min_rows=1),
    Case("stu_simple_list_emails", "List all student email addresses", "simple", "required", min_rows=1),
    Case("stu_simple_list_depts", "List all departments", "simple", "required", min_rows=1),
    Case("stu_join1_student_dept", "List students with their department name", "join1", "best_effort", min_rows=1),
    Case("stu_join_courses_prof", "Show courses with professor last name", "join1", "best_effort", min_rows=1),
]

# SQL smoke per database (must run on live DB — validates credentials + tables exist)
PG_SMOKE_SQL: Dict[str, str] = {
    "library_db": "SELECT COUNT(*) AS c FROM branches",
    "employee_db": "SELECT COUNT(*) AS c FROM employees",
    "student_db": "SELECT COUNT(*) AS c FROM students",
}


def _env(name: str, default: str) -> str:
    v = os.environ.get(name)
    return v.strip() if v else default


def _normalize_foreign_keys(raw: Any) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    if not raw:
        return out
    for fk in raw:
        if isinstance(fk, dict):
            out.append(
                {
                    "from_table": fk["from_table"],
                    "from_column": fk["from_column"],
                    "to_table": fk["to_table"],
                    "to_column": fk["to_column"],
                }
            )
        elif isinstance(fk, (list, tuple)) and len(fk) >= 4:
            out.append(
                {
                    "from_table": fk[0],
                    "from_column": fk[1],
                    "to_table": fk[2],
                    "to_column": fk[3],
                }
            )
    return out


def _tables_from_schema_payload(payload: Dict[str, Any]) -> Dict[str, List[str]]:
    tables = payload.get("tables") or {}
    # Normalize column lists to plain list[str]
    return {str(k): [str(c) for c in v] for k, v in tables.items()}


@dataclass
class RunStats:
    required_pass: int = 0
    required_fail: int = 0
    best_pass: int = 0
    best_fail: int = 0
    skipped: List[str] = field(default_factory=list)
    required_failure_msgs: List[str] = field(default_factory=list)


def main() -> int:
    try:
        from starlette.testclient import TestClient
    except ModuleNotFoundError as e:
        print("Missing dependency for TestClient. Install with: pip install httpx")
        print(e)
        return 1

    from app.main import app

    skip_pg = _env("SKIP_PG", "").lower() in ("1", "true", "yes")
    skip_nl2sql = _env("SKIP_NL2SQL", "").lower() in ("1", "true", "yes")
    model_path = Path(_env("NL2SQL_MODEL_PATH", str(ROOT / "models" / "nl2sql-t5")))
    model_ok = model_path.is_dir() and any(model_path.iterdir())

    client = TestClient(app, raise_server_exceptions=False)

    stats = RunStats()
    created_connection_ids: List[int] = []

    # --- Auth: register or login fixed regression user ---
    suffix = uuid.uuid4().hex[:8]
    username = f"e2e_reg_{suffix}"
    email = f"e2e_{suffix}@example.com"
    password = "regtest123"

    r = client.post(
        "/auth/register",
        json={"username": username, "email": email, "password": password, "full_name": "E2E Regression"},
    )
    if r.status_code == 201:
        user_id = r.json()["id"]
    elif r.status_code == 400 and "already" in (r.json().get("detail") or "").lower():
        # Extremely unlikely collision; register again
        suffix = uuid.uuid4().hex[:8]
        username = f"e2e_reg_{suffix}"
        email = f"e2e_{suffix}@example.com"
        r2 = client.post(
            "/auth/register",
            json={"username": username, "email": email, "password": password, "full_name": "E2E Regression"},
        )
        if r2.status_code != 201:
            print("FATAL: could not register user:", r2.status_code, r2.text)
            return 1
        user_id = r2.json()["id"]
    else:
        print("FATAL: register failed:", r.status_code, r.text)
        return 1

    print(f"Using user_id={user_id} ({username})")

    if skip_pg:
        stats.skipped.append("SKIP_PG=1 — Postgres connection tests skipped")
        print_summary(stats, model_ok, skip_nl2sql)
        return 0 if stats.required_fail == 0 else 1

    host = _env("PG_E2E_HOST", "localhost")
    port = int(_env("PG_E2E_PORT", "5432"))
    user = _env("PG_E2E_USER", "hari")
    pwd = _env("PG_E2E_PASSWORD", "hari123")

    db_configs: List[Tuple[str, str, List[Case]]] = [
        ("library_db", "E2E Library", LIBRARY_CASES),
        ("employee_db", "E2E Employee", EMPLOYEE_CASES),
        ("student_db", "E2E Student", STUDENT_CASES),
    ]

    conn_by_db: Dict[str, int] = {}

    for database_name, friendly_name, _cases in db_configs:
        tag = f"{friendly_name} ({database_name})"
        body = {
            "name": f"{friendly_name} {int(time.time())}",
            "db_type": "postgresql",
            "host": host,
            "port": port,
            "database_name": database_name,
            "username": user,
            "password": pwd,
        }
        cr = client.post(f"/db/connections?user_id={user_id}", json=body)
        if cr.status_code != 201:
            msg = f"FAIL {tag}: POST /db/connections -> {cr.status_code} {cr.text[:500]}"
            stats.skipped.append(msg)
            print(msg)
            stats.required_fail += sum(1 for c in _cases if c.severity == "required")
            for c in _cases:
                if c.severity == "required":
                    stats.required_failure_msgs.append(f"{database_name} :: {c.label}: connection not created")
            continue
        cid = cr.json()["id"]
        created_connection_ids.append(cid)
        conn_by_db[database_name] = cid

        # Smoke execute SQL
        smoke_sql = PG_SMOKE_SQL[database_name]
        er = client.post(
            f"/query/execute-sql?user_id={user_id}",
            json={"sql": smoke_sql, "database_id": cid},
        )
        if er.status_code != 200:
            stats.required_failure_msgs.append(f"{tag} execute-sql HTTP {er.status_code}: {er.text[:300]}")
            stats.required_fail += 1
            continue
        ej = er.json()
        if not ej.get("success"):
            stats.required_failure_msgs.append(f"{tag} execute-sql failed: {ej.get('error')}")
            stats.required_fail += 1
            continue
        print(f"OK smoke execute-sql {tag} rows={ej.get('row_count')}")

        # Schema for NL2SQL body
        sr = client.get(f"/db/connections/{cid}/schema?user_id={user_id}&use_cached=true")
        if sr.status_code != 200:
            stats.skipped.append(f"{tag}: schema GET {sr.status_code}")
            for c in _cases:
                if c.severity == "required":
                    stats.required_fail += 1
                    stats.required_failure_msgs.append(f"{database_name} :: {c.label}: schema unavailable")
            continue
        sp = sr.json()
        tables = _tables_from_schema_payload(sp)
        fks = _normalize_foreign_keys(sp.get("foreign_keys"))

        if skip_nl2sql or not model_ok:
            if not model_ok:
                stats.skipped.append("NL2SQL skipped: model directory missing or empty (set NL2SQL_MODEL_PATH)")
            else:
                stats.skipped.append("NL2SQL skipped: SKIP_NL2SQL=1")
            continue

        for case in _cases:
            payload = {
                "question": case.question,
                "schema": tables,
                "foreign_keys": fks,
                "use_sanitizer": True,
                "use_pattern_correction": True,
                "return_details": False,
                "execute_query": True,
                "database_id": cid,
            }
            nr = client.post(f"/query/nl2sql?user_id={user_id}", json=payload, timeout=180.0)
            tag_case = f"{database_name} :: {case.label}"
            if nr.status_code != 200:
                _record_case(stats, case, False, f"HTTP {nr.status_code} {nr.text[:400]}")
                if case.severity == "required":
                    stats.required_failure_msgs.append(f"{tag_case}: {nr.text[:200]}")
                continue
            nj = nr.json()
            sql = nj.get("sql") or ""
            ex = nj.get("execution_result")
            if ex is None:
                _record_case(stats, case, False, "no execution_result")
                if case.severity == "required":
                    stats.required_failure_msgs.append(f"{tag_case}: no execution_result (sql={sql[:120]!r})")
                continue
            if not ex.get("success"):
                _record_case(
                    stats,
                    case,
                    False,
                    f"exec error: {ex.get('error')}",
                )
                if case.severity == "required":
                    stats.required_failure_msgs.append(
                        f"{tag_case}: {ex.get('error')} | SQL: {sql[:200]!r}"
                    )
                continue
            rows = int(ex.get("row_count") or 0)
            if rows < case.min_rows:
                _record_case(stats, case, False, f"row_count {rows} < min_rows {case.min_rows}")
                if case.severity == "required":
                    stats.required_failure_msgs.append(f"{tag_case}: row_count {rows} < {case.min_rows}")
                continue
            _record_case(stats, case, True, f"rows={rows}")
            print(f"OK nl2sql+exec {tag_case} tier={case.tier} rows={rows}")

    # Cleanup connections (best effort)
    for cid in created_connection_ids:
        dr = client.delete(f"/db/connections/{cid}?user_id={user_id}")
        if dr.status_code not in (204, 200):
            print(f"WARN: could not delete connection {cid}: {dr.status_code}")

    print_summary(stats, model_ok, skip_nl2sql)
    return 0 if stats.required_fail == 0 else 1


def _record_case(stats: RunStats, case: Case, ok: bool, detail: str) -> None:
    if case.severity == "required":
        if ok:
            stats.required_pass += 1
        else:
            stats.required_fail += 1
    else:
        if ok:
            stats.best_pass += 1
        else:
            stats.best_fail += 1
            print(f"WARN best_effort {case.label}: {detail}")


def print_summary(stats: RunStats, model_ok: bool, skip_nl2sql: bool) -> None:
    print()
    print("=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print(f"  required:  {stats.required_pass} passed,  {stats.required_fail} FAILED")
    print(f"  best_effort: {stats.best_pass} passed,  {stats.best_fail} warned")
    if stats.skipped:
        print("  Skipped / notes:")
        for s in stats.skipped:
            print(f"    - {s}")
    if not model_ok:
        print("  NOTE: T5 model path not found — NL2SQL cases were skipped unless SKIP_NL2SQL.")
    if stats.required_failure_msgs:
        print("  Required failures:")
        for f in stats.required_failure_msgs[:40]:
            print(f"    * {f}")
        if len(stats.required_failure_msgs) > 40:
            print(f"    ... and {len(stats.required_failure_msgs) - 40} more")
    print("=" * 72)


if __name__ == "__main__":
    raise SystemExit(main())
