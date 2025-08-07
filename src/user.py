from fastapi import Depends, APIRouter
from models import auth_required_responses
from gotrue import User
from auth import verify_user

user_router = APIRouter(prefix="/user", tags=["user"])


@user_router.get(
    "/",
    response_model=dict,
    responses=auth_required_responses,
)
def get_user(user: User = Depends(verify_user)):
    return user.model_dump()


@user_router.get(
    "/email/",
    response_model=str,
    responses=auth_required_responses,
    description="Fetches user email from supabase based on jwt provided in the authorization header. Test this endpoint to check if the jwt is valid.",
)
def get_user_email(user: User = Depends(verify_user)):
    return user.email
