from fastapi import APIRouter
from supabase_client import db_client

user_router = APIRouter(prefix="/user", tags=["user"])


@user_router.get("/", response_model=str)
def read_user():
    user = db_client.table("users").select("*").execute()
    if not user.data:
        return {"error": "User not found"}
    return user.data[0].get("name")  # Assuming the first user is returned
