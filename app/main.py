from fastapi import FastAPI
from app import models
from app.routers import concerts, ws, users, authentication

app = FastAPI()

app.include_router(ws.router)
app.include_router(users.router)
app.include_router(authentication.router)
app.include_router(concerts.router)