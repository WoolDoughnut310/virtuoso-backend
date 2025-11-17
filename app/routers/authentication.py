from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import Depends, APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pwdlib import PasswordHash
from app.config import settings
from app.dependencies.db import SessionDep
from fastapi.responses import JSONResponse
from app.models.user import User, UserPublic, UserCreate
from sqlmodel import select
import jwt


password_hash = PasswordHash.recommended()

router = APIRouter()


def authenticate(username: str, password: str, session: SessionDep):
    user = session.exec(select(User).where(User.username == username)).first()
    if not user:
        return False
    if not password_hash.verify(password, user.hashed_password):
        return False
    return user


@router.post("/token")
async def login_user(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session: SessionDep
):
    user = authenticate(form_data.username, form_data.password, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = jwt.encode(
        {
            "sub": user.username,
            "exp": datetime.now(timezone.utc)
            + timedelta(minutes=settings.access_token_expire_minutes),
        },
        settings.secret_key,
        algorithm=settings.algorithm,
    )

    response = JSONResponse({"message": "Logged in"})
    response.set_cookie(
        "access_token", token
    )
    return response

@router.post("/register", response_model=UserPublic)
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

    return user_db