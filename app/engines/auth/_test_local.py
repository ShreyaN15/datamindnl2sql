"""Simple local test script for the auth engine.

Run this directly (python -m app.engines.auth._test_local) to exercise the
pure-Python engine functions without FastAPI.
"""
from . import service


def _run():
    email = "tester@example.com"
    password = "strong_password"

    try:
        print("Creating user...", service.create_user(email, password))
    except ValueError as e:
        print("Create user error (expected if already exists):", e)

    try:
        token_resp = service.authenticate_user(email, password)
        print("Authenticated:", token_resp)
        token = token_resp["access_token"]

        print("Session context:", service.get_session_context(token))

        db_info = {
            "db_type": "postgres",
            "host": "localhost",
            "port": 5432,
            "username": "user",
            "password": "pass",
            "database": "school",
        }
        print("Set active DB:", service.set_active_database(token, db_info))
        print("Session after set_db:", service.get_session_context(token))

        print("Logging out:", service.logout(token))
    except Exception as e:
        print("Error during auth flow:", e)


if __name__ == "__main__":
    _run()
