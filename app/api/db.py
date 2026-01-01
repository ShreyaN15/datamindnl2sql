from fastapi import APIRouter

router = APIRouter()

@router.post("/test-connection")
def test_connection_stub():
    return {"message": "db connection test not implemented"}
