from __future__ import annotations

import os
import threading
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import (Column, DateTime, String, Table, create_engine,
						insert, select)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import registry, Session
import json

import redis
from app.core import security as core_security

# Simple SQLAlchemy mapping for a lightweight users table.
mapper_registry = registry()

# lazily create engines per DSN so tests can monkeypatch AUTH_DB_URL at runtime
_engine_cache: Dict[str, object] = {}


def _get_engine():
	dsn = os.getenv("AUTH_DB_URL", "sqlite:///./auth_users.db")
	if dsn not in _engine_cache:
		_engine_cache[dsn] = create_engine(dsn, echo=False, future=True)
	return _engine_cache[dsn]

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

JWT_SECRET = os.getenv("AUTH_JWT_SECRET", "dev-secret-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXP_DELTA_SECONDS = int(os.getenv("AUTH_JWT_EXP_SECONDS", "3600"))

_sessions_lock = threading.Lock()
# in-memory sessions (fallback)
_sessions: Dict[str, Dict] = {}

# optional Redis session store
_redis = None
_redis_url = os.getenv("REDIS_URL")
if _redis_url:
	try:
		_redis = redis.Redis.from_url(_redis_url, decode_responses=True)
		# test connection lazily; don't fail at import time
	except Exception:
		_redis = None


users_table = Table(
	"auth_users",
	mapper_registry.metadata,
	Column("id", String, primary_key=True),
	Column("email", String, unique=True, nullable=False),
	Column("password_hash", String, nullable=False),
	Column("created_at", DateTime, default=datetime.utcnow),
)


def _ensure_tables() -> None:
	# ensure tables exist on the current engine (based on AUTH_DB_URL)
	mapper_registry.metadata.create_all(_get_engine())


def _hash_password(password: str) -> str:
	return pwd_context.hash(password)


def _verify_password(password: str, hash: str) -> bool:
	return pwd_context.verify(password, hash)


def create_user(email: str, password: str) -> Dict[str, str]:
	"""Create a user in the auth users DB.

	Returns a simple message dict on success. Raises on conflict.
	"""
	_ensure_tables()
	user_id = str(uuid.uuid4())
	password_hash = _hash_password(password)
	with Session(_get_engine()) as session:
		try:
			stmt = insert(users_table).values(
				id=user_id, email=email, password_hash=password_hash
			)
			session.execute(stmt)
			session.commit()
		except IntegrityError:
			session.rollback()
			raise ValueError("user already exists")

	return {"message": "account created", "user_id": user_id}


def authenticate_user(email: str, password: str) -> Dict[str, str]:
	"""Verify credentials and create a JWT + session entry.

	Returns a dict with `access_token` and `token_type`.
	"""
	_ensure_tables()
	with Session(_get_engine()) as session:
		stmt = select(users_table).where(users_table.c.email == email)
		row = session.execute(stmt).mappings().first()
		if not row:
			raise ValueError("invalid credentials")
		user_id = row["id"]
		stored_hash = row["password_hash"]
		if not _verify_password(password, stored_hash):
			raise ValueError("invalid credentials")

	# create JWT
	now = datetime.utcnow()
	payload = {
		"sub": user_id,
		"email": email,
		"iat": int(now.timestamp()),
		"exp": int((now + timedelta(seconds=JWT_EXP_DELTA_SECONDS)).timestamp()),
	}
	token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

	# create session context
	session_obj = {
		"user_id": user_id,
		"email": email,
		"created_at": now.isoformat(),
		"active_db": None,
		"last_query": None,
	}
	with _sessions_lock:
		_sessions[token] = session_obj

	return {"access_token": token, "token_type": "bearer"}


def _get_session(token: str) -> Dict:
	# prefer Redis if configured
	if _redis is not None:
		val = _redis.get(f"session:{token}")
		if not val:
			raise ValueError("invalid or expired session token")
		return json.loads(val)

	with _sessions_lock:
		s = _sessions.get(token)
		if s is None:
			raise ValueError("invalid or expired session token")
		return s


def create_session(user_id: str, email: str) -> str:
	"""Create a programmatic session (returns token)."""
	now = datetime.utcnow()
	payload = {
		"sub": user_id,
		"email": email,
		"iat": int(now.timestamp()),
		"exp": int((now + timedelta(seconds=JWT_EXP_DELTA_SECONDS)).timestamp()),
	}
	token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
	session_obj = {
		"user_id": user_id,
		"email": email,
		"created_at": now.isoformat(),
		"active_db": None,
		"last_query": None,
	}
	if _redis is not None:
		_redis.set(f"session:{token}", json.dumps(session_obj), ex=JWT_EXP_DELTA_SECONDS)
	else:
		with _sessions_lock:
			_sessions[token] = session_obj
	return token


def get_session_context(token: str) -> Dict[str, Optional[str]]:
	"""Return the session context for a token."""
	s = _get_session(token)
	# Sanitize active_db before returning so callers don't receive raw credentials
	active_db = s.get("active_db")
	if isinstance(active_db, dict):
		safe_active_db = {k: v for k, v in active_db.items() if k != "password" and k != "password_enc"}
	else:
		safe_active_db = active_db

	return {
		"user_id": s["user_id"],
		"email": s["email"],
		"active_db": safe_active_db,
		"last_query": s.get("last_query"),
	}


def get_db_credentials(token: str) -> Dict[str, str]:
	"""Return decrypted DB credentials for internal use by the Auth engine.

	IMPORTANT: This function is intended to be used only by code that has
	explicit authorization to access raw credentials (e.g., a DB connection
	helper owned by the execution engine through a controlled interface).
	Other engines should NOT call this directly.
	"""
	s = _get_session(token)
	active_db = s.get("active_db") or {}
	username = active_db.get("username")
	database = active_db.get("database")
	host = active_db.get("host")
	port = active_db.get("port")
	db_type = active_db.get("db_type")

	# retrieve password (decrypt if necessary)
	pw = None
	if "password_enc" in active_db:
		try:
			pw = core_security.decrypt_value(active_db["password_enc"])
		except Exception:
			raise ValueError("failed to decrypt stored password")
	else:
		pw = active_db.get("password")

	return {
		"db_type": db_type,
		"host": host,
		"port": port,
		"username": username,
		"password": pw,
		"database": database,
	}


def set_active_database(token: str, db_info: Dict) -> Dict[str, str]:
	"""Validate and attach DB connection info to session context.

	This function DOES NOT open connections or run queries. It only stores
	validated metadata per guidelines.
	"""
	# minimal validation
	expected = {"db_type", "host", "port", "username", "password", "database"}
	if not expected.issubset(set(db_info.keys())):
		raise ValueError("invalid db_info; missing fields")

	s = _get_session(token)

	# encrypt sensitive fields if encryption key is configured
	enc = None
	try:
		# only encrypt the password field
		password = db_info.get("password")
		if password is not None:
			try:
				enc = core_security.encrypt_value(password)
			except RuntimeError:
				enc = None
	except Exception:
		enc = None

	stored = {
		"db_type": db_info["db_type"],
		"dsn": f"{db_info['db_type']}://{db_info['username']}@{db_info['host']}:{db_info['port']}/{db_info['database']}",
	}
	if enc:
		stored["password_enc"] = enc
	else:
		stored["password"] = db_info.get("password")

	# store back to session (Redis or in-memory)
	if _redis is not None:
		# fetch, modify, write back
		cur = _redis.get(f"session:{token}")
		if not cur:
			raise ValueError("invalid or expired session token")
		cur_obj = json.loads(cur)
		cur_obj["active_db"] = stored
		_redis.set(f"session:{token}", json.dumps(cur_obj), ex=JWT_EXP_DELTA_SECONDS)
	else:
		with _sessions_lock:
			s["active_db"] = stored
	return {"message": "database connected"}


def logout(token: str) -> Dict[str, str]:
	if _redis is not None:
		_redis.delete(f"session:{token}")
	else:
		with _sessions_lock:
			_sessions.pop(token, None)
	return {"message": "logged out"}


def verify_token(token: str) -> Dict:
	"""Verify JWT signature and expiration; returns payload."""
	try:
		payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
		return payload
	except JWTError as exc:
		raise ValueError("invalid token") from exc


