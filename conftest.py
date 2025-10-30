from fastapi.testclient import TestClient
from main import app
from database import engine
from sqlmodel import Session
import pytest

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture
def session():
    with Session(engine) as session:
        yield session

@pytest.fixture
def websocket(client):
    with client.websocket_connect("/ws") as ws:
        yield ws