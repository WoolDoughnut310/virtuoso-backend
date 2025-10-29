from datetime import datetime, timedelta, timezone
from typing import Annotated
import jwt
from fastapi import Depends, APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pwdlib import PasswordHash
from .config import settings
from .db import get_user, CursorDep
from .models.token import Token


password_hash = PasswordHash.recommended()

router = APIRouter()

async def authenticate(username: str, password: str, cur: CursorDep):
    user = await get_user(username, cur)
    if not user:
        return False
    if not password_hash.verify(password, user.hashed_password):
        return False
    return user

@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    cur: CursorDep
) -> Token:
    user = await authenticate(form_data.username, form_data.password, cur)
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

