from typing import Annotated
from fastapi import Depends, APIRouter
from ..models.user import User, UserPublic, UserCreate
from ..dependencies import get_current_user
from ..database import SessionDep
from ..auth import password_hash

router = APIRouter()


@router.get("/me", response_model=UserPublic)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return current_user

@router.get("/register", response_model=UserPublic)
async def register_user(
    user: UserCreate,
    session: SessionDep
):
    user_data = user.model_dump(exclude_unset=True)
    user_data["hashed_password"] = password_hash.hash(user_data.pop("password"))
    
    user_db = User(**user_data)
    session.add(user_db)
    session.commit()
    session.refresh(user_db)

    return user