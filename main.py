from fastapi import FastAPI
from fastapi import FastAPI
from contextlib import asynccontextmanager
from .db import init_pool, close_pool
from .routers import ws
from .routers import users


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pool()
    yield
    await close_pool()

app = FastAPI()

app.include_router(ws.router)
app.include_router(users.router)