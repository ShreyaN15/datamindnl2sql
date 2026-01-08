from typing import Dict

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.engines.auth import service as auth_service

router = APIRouter()


def _get_bearer_token(authorization: str | None = Header(default=None)) -> str:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing authorization header")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid authorization header")
    return parts[1]


def require_auth(token: str = Depends(_get_bearer_token)) -> Dict:
    try:
        # verify token signature and presence
        auth_service.verify_token(token)
        return auth_service.get_session_context(token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid or expired token")


@router.post("/")
def query_stub(session_ctx: Dict = Depends(require_auth)):
    # session_ctx is available and validated; downstream engines should use it read-only
    return {"message": "query pipeline not implemented", "session": session_ctx}
