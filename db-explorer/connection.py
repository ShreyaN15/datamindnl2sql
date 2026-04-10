"""Build SQLAlchemy URLs from connection fields (mirrors DataMind connection shape, no app imports)."""

from __future__ import annotations

from typing import Optional
from urllib.parse import quote_plus


def build_sqlalchemy_url(
    db_type: str,
    host: Optional[str],
    port: Optional[int],
    database_name: str,
    username: Optional[str],
    password: Optional[str],
) -> str:
    t = (db_type or "").lower().strip()
    if t == "sqlite":
        return f"sqlite:///{database_name}"

    default_ports = {"mysql": 3306, "postgresql": 5432, "mssql": 1433, "oracle": 1521}
    p = port if port is not None else default_ports.get(t, 5432)
    h = host or "localhost"

    if t == "mysql":
        driver = "mysql+pymysql"
    elif t == "postgresql":
        driver = "postgresql+psycopg2"
    else:
        raise ValueError(
            f"Database type '{db_type}' is not supported in this demo explorer. "
            "Use postgresql, mysql, or sqlite."
        )

    if username and password:
        auth = f"{quote_plus(username)}:{quote_plus(password)}@"
    elif username:
        auth = f"{quote_plus(username)}@"
    else:
        auth = ""

    return f"{driver}://{auth}{h}:{p}/{database_name}"
