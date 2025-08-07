from fastapi import Depends, APIRouter
from gotrue import User
from src.util.models import unauth_res
from src.util.auth import verify_user

user_router = APIRouter(prefix="/user", tags=["user"])


@user_router.get(
    "/",
    response_model=User,
    responses=unauth_res,
)
def get_user(user: User = Depends(verify_user)):
    return user


@user_router.get(
    "/email/",
    response_model=str,
    responses=unauth_res,
    description="Fetches user email from supabase based on jwt provided in the authorization header. Test this endpoint to check if the jwt is valid.",
)
def get_user_email(user: User = Depends(verify_user)):
    return user.email
