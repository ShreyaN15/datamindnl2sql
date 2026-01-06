from __future__ import annotations

import os
import base64
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken


def _get_fernet() -> Optional[Fernet]:
	key = os.getenv("APP_ENCRYPTION_KEY")
	if not key:
		return None
	# Allow raw key or base64
	try:
		# if key length looks like base64
		f = Fernet(key)
		return f
	except Exception:
		# try to derive a Fernet key from raw bytes
		k = base64.urlsafe_b64encode(key.encode("utf-8"))
		try:
			return Fernet(k)
		except Exception:
			return None


def encrypt_value(plaintext: str) -> str:
	f = _get_fernet()
	if f is None:
		raise RuntimeError("APP_ENCRYPTION_KEY not configured")
	return f.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_value(token: str) -> str:
	f = _get_fernet()
	if f is None:
		raise RuntimeError("APP_ENCRYPTION_KEY not configured")
	try:
		return f.decrypt(token.encode("utf-8")).decode("utf-8")
	except InvalidToken as exc:
		raise ValueError("invalid encrypted value") from exc
