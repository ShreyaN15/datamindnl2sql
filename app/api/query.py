from fastapi import APIRouter

router = APIRouter()

@router.post("/")
def query_stub():
    return {
        "message": "query pipeline not implemented"
    }
