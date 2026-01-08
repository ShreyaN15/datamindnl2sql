from typing import Dict

from fastapi import APIRouter, Header, HTTPException, Request, status

from app.engines.auth import service as auth_service

router = APIRouter()


def _extract_bearer(auth_header: str | None) -> str:
    if not auth_header:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing authorization header")
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid authorization header")
    return parts[1]


@router.post("/signup")
def signup(payload: Dict):
    try:
        email = payload["email"]
        password = payload["password"]
    except KeyError:
        raise HTTPException(status_code=400, detail="email and password required")
    try:
        return auth_service.create_user(email, password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
def login(payload: Dict):
    try:
        email = payload["email"]
        password = payload["password"]
    except KeyError:
        raise HTTPException(status_code=400, detail="email and password required")
    try:
        return auth_service.authenticate_user(email, password)
    except ValueError:
        raise HTTPException(status_code=401, detail="invalid credentials")


@router.post("/logout")
def logout(authorization: str | None = Header(default=None)):
    token = _extract_bearer(authorization)
    return auth_service.logout(token)


@router.get("/session/me")
def session_me(authorization: str | None = Header(default=None)):
    token = _extract_bearer(authorization)
    try:
        return auth_service.get_session_context(token)
    except ValueError:
        raise HTTPException(status_code=401, detail="invalid session")


@router.post("/session/set-db")
async def session_set_db(request: Request, authorization: str | None = Header(default=None)):
    token = _extract_bearer(authorization)
    db_info = await request.json()
    try:
        return auth_service.set_active_database(token, db_info)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
