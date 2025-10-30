from sqlmodel import Session, SQLModel, create_engine
from .config import settings
from typing import Annotated
from fastapi import Depends

DB_URL = f"postgresql://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(DB_URL, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
    

SessionDep = Annotated[Session, Depends(get_session)]