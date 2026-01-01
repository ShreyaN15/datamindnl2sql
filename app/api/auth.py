from fastapi import APIRouter

router = APIRouter()

@router.post("/login")
def login_stub():
    return {"message": "login not implemented"}

@router.post("/signup")
def signup_stub():
    return {"message": "signup not implemented"}
