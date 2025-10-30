from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import Depends, APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pwdlib import PasswordHash
from config import settings
from models.token import Token
from database import SessionDep
from models.user import User
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
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: SessionDep
) -> Token:
    user = authenticate(form_data.username, form_data.password, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = jwt.encode({
        "sub": user.username,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes),
    }, settings.secret_key, algorithm=settings.algorithm)

    return Token(access_token=access_token, token_type="bearer")

