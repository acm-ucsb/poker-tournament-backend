from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from src.util.supabase_client import db_client

bearer_scheme = HTTPBearer()


# this function verifies the jwt token provided in the authorization header, returns the user object
# pass into endpoint as (<other_params>, user: User = Depends(verify_user))
def verify_user(
    http_auth: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    jwt = http_auth.credentials
    err = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    try:
        # verify the jwt, supabase will check with the secret key
        user_response = db_client.auth.get_user(jwt)
    except Exception:
        raise err

    if not user_response:
        raise err
    return user_response.user


def verify_admin_user(http_auth: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    user = verify_user(http_auth)

    is_admin_res = (
        db_client.table("users").select("is_admin").eq("id", user.id).single().execute()
    )

    if not is_admin_res.data["is_admin"]:
        raise HTTPException(401, detail="user is not admin")

    return user
