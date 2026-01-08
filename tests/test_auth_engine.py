import os
import tempfile
import base64

from app.engines.auth import service as auth_service


def test_create_and_authenticate(tmp_path, monkeypatch):
    # use temporary sqlite db for tests
    db_file = tmp_path / "test_auth.db"
    monkeypatch.setenv("AUTH_DB_URL", f"sqlite:///{db_file}")

    # set encryption key
    key = base64.urlsafe_b64encode(b"test-secret-key-32bytes!!test").decode()
    monkeypatch.setenv("APP_ENCRYPTION_KEY", key)

    # create user
    email = "ci-test@example.com"
    password = "ci-password"
    res = auth_service.create_user(email, password)
    assert "user_id" in res

    # authenticate
    token_resp = auth_service.authenticate_user(email, password)
    assert "access_token" in token_resp
    token = token_resp["access_token"]

    # get session
    ctx = auth_service.get_session_context(token)
    assert ctx["email"] == email

    # set active database (should store encrypted pw)
    db_info = {
        "db_type": "postgres",
        "host": "localhost",
        "port": 5432,
        "username": "u",
        "password": "s3cret",
        "database": "db",
    }
    resp = auth_service.set_active_database(token, db_info)
    assert resp["message"] == "database connected"

    # logout
    r = auth_service.logout(token)
    assert r["message"] == "logged out"
