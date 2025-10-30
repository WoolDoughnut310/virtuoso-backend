from fastapi import FastAPI
from fastapi import FastAPI
from contextlib import asynccontextmanager
from .database import create_db_and_tables
from . import models
from .routers import ws, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield    

app = FastAPI()

app.include_router(ws.router)
app.include_router(users.router)