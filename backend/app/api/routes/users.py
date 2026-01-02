from fastapi import APIRouter

router = APIRouter(tags=["users"])

@router.get("/me")
async def read_users_me():
    return {"username": "admin"}
