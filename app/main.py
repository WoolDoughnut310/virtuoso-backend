from fastapi import FastAPI
from app import models
from app.routers import concerts, ws, users, authentication
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.dependencies.scheduler import get_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = get_scheduler()
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(ws.router)
app.include_router(users.router)
app.include_router(authentication.router)
app.include_router(concerts.router)