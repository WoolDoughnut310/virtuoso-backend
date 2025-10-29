from typing import Annotated
from fastapi import Depends, APIRouter
from ..models.user import User
from ..dependencies import get_current_user

router = APIRouter()


@router.get("/users/me/", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return current_user