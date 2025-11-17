from fastapi import APIRouter
from app.models.user import UserPublic
from app.dependencies.users import CurrentUserDep

router = APIRouter()


@router.get("/me", response_model=UserPublic)
async def read_users_me(
    user: CurrentUserDep,
):
    return user