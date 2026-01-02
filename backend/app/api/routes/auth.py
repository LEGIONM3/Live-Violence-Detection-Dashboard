from fastapi import APIRouter

router = APIRouter(tags=["auth"])

@router.post("/login")
async def login():
    return {"token": "mock-token"}
