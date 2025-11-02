from fastapi import HTTPException, status
from app.routers.users import CurrentUserDep

def check_artist(user: CurrentUserDep):
    print("user", user)
    if not user.is_artist:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return True