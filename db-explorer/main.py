"""
Standalone read-only DB explorer API for demos.
Only runs fixed SELECT patterns; table names must come from introspection.
"""

from __future__ import annotations

import re
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

from connection import build_sqlalchemy_url

STATIC_DIR = str(Path(__file__).resolve().parent / "static")

TABLE_NAME_RE = re.compile(r"^[A-Za-z0-9_]+$")


@dataclass
class ConnectionState:
    engine: Engine
    db_type: str
    display_name: str
    database_name: str
    table_names: List[str] = field(default_factory=list)


_connections: Dict[str, ConnectionState] = {}
_connections_lock = Lock()
MAX_CONNECTIONS = 32


def _dispose_oldest_connection() -> None:
    if len(_connections) < MAX_CONNECTIONS:
        return
    oldest = next(iter(_connections.keys()))
    st = _connections.pop(oldest, None)
    if st:
        st.engine.dispose()


class ConnectBody(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    db_type: str = "postgresql"
    host: Optional[str] = "localhost"
    port: Optional[int] = None
    database_name: str = Field(..., min_length=1, max_length=500)
    username: Optional[str] = ""
    password: Optional[str] = ""


def _create_engine_from_body(body: ConnectBody) -> Engine:
    t = body.db_type.lower().strip()
    if t in ("mssql", "oracle"):
        raise HTTPException(
            status_code=400,
            detail="MS SQL and Oracle are not enabled in this demo. Use PostgreSQL, MySQL, or SQLite.",
        )
    try:
        url = build_sqlalchemy_url(
            db_type=body.db_type,
            host=body.host if t != "sqlite" else None,
            port=body.port,
            database_name=body.database_name,
            username=body.username or None,
            password=body.password or None,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    connect_args: Dict[str, Any] = {}
    if "sqlite" not in url:
        connect_args["connect_timeout"] = 10

    return create_engine(url, pool_pre_ping=True, connect_args=connect_args)


def _quote_table(engine: Engine, table: str) -> str:
    if not TABLE_NAME_RE.match(table):
        raise HTTPException(status_code=400, detail="Invalid table name")
    return engine.dialect.identifier_preparer.quote(table)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    with _connections_lock:
        for st in _connections.values():
            st.engine.dispose()
        _connections.clear()


app = FastAPI(title="DB Explorer (demo)", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/connect")
def api_connect(body: ConnectBody):
    engine = _create_engine_from_body(body)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        engine.dispose()
        raise HTTPException(status_code=400, detail=f"Connection failed: {e}") from e

    insp = inspect(engine)
    tables = sorted(insp.get_table_names())

    cid = str(uuid.uuid4())
    with _connections_lock:
        _dispose_oldest_connection()
        _connections[cid] = ConnectionState(
            engine=engine,
            db_type=body.db_type.lower(),
            display_name=body.name,
            database_name=body.database_name,
            table_names=tables,
        )

    return {
        "connection_id": cid,
        "name": body.name,
        "db_type": body.db_type.lower(),
        "database_name": body.database_name,
        "table_count": len(tables),
    }


@app.get("/api/connections")
def api_list_connections():
    with _connections_lock:
        items = [
            {
                "id": cid,
                "name": st.display_name,
                "db_type": st.db_type,
                "database_name": st.database_name,
                "table_count": len(st.table_names),
            }
            for cid, st in _connections.items()
        ]
    return {"connections": items}


@app.delete("/api/connections/{connection_id}")
def api_remove_connection(connection_id: str):
    with _connections_lock:
        st = _connections.pop(connection_id, None)
    if st:
        st.engine.dispose()
    return {"ok": True}


@app.get("/api/connections/{connection_id}/tables")
def api_list_tables(connection_id: str):
    st = _get_connection(connection_id)
    preparer = st.engine.dialect.identifier_preparer
    rows: List[Dict[str, Any]] = []
    with st.engine.connect() as conn:
        for t in st.table_names:
            q = preparer.quote(t)
            try:
                cnt = conn.execute(text(f"SELECT COUNT(*) AS c FROM {q}")).scalar()
            except Exception:
                cnt = None
            rows.append({"name": t, "row_count": cnt})
    return {"tables": rows}


@app.get("/api/connections/{connection_id}/tables/{table_name}/preview")
def api_preview(connection_id: str, table_name: str):
    st = _get_connection(connection_id)
    if table_name not in st.table_names:
        raise HTTPException(status_code=404, detail="Unknown table")

    qtable = _quote_table(st.engine, table_name)

    with st.engine.connect() as conn:
        result = conn.execute(text(f"SELECT * FROM {qtable} LIMIT 100"))
        keys = list(result.keys())
        data_rows = [dict(zip(keys, row)) for row in result.fetchall()]

    return {"columns": keys, "rows": data_rows}


def _get_connection(connection_id: str) -> ConnectionState:
    with _connections_lock:
        st = _connections.get(connection_id)
    if not st:
        raise HTTPException(
            status_code=404,
            detail="Connection not found. It may have been removed or the server was restarted.",
        )
    return st


@app.get("/")
def index():
    return FileResponse(f"{STATIC_DIR}/index.html")
