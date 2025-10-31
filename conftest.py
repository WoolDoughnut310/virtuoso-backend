from fastapi.testclient import TestClient
from main import app
from database import engine
from sqlmodel import Session
import pytest
from models.user import User
from pwdlib import PasswordHash
from dependencies import get_media_path

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

@pytest.fixture
def make_test_user(session):
    password_hash = PasswordHash.recommended()

    def _make_test_user(password: str = "securepassword", is_artist: bool = False) -> User:
        user = User(
            username="testuser",
            email="testuser@accounts.com",
            full_name="Test User",
            hashed_password=password_hash.hash(password),
            is_artist=is_artist
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    
    return _make_test_user

@pytest.fixture
def media_path(tmp_path):
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    app.dependency_overrides[get_media_path] = lambda: str(media_dir)
    return media_dir