from database import engine
from typing import Annotated
from fastapi import Depends
from sqlmodel import Session

def get_session():
    with Session(engine) as session:
        yield session
    

SessionDep = Annotated[Session, Depends(get_session)]