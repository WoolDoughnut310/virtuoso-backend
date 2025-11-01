from fastapi import FastAPI
from contextlib import asynccontextmanager
from database import create_db_and_tables
import models
from routers import concerts, ws, users, authentication


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI()

app.include_router(ws.router)
app.include_router(users.router)
app.include_router(authentication.router)
app.include_router(concerts.router)