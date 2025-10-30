from pwdlib import PasswordHash
from models.user import User

password_hash = PasswordHash.recommended()

def test_login_success(client, session):
    password = "securepassword"
    user = User(
        username="testuser",
        email="testuser@accounts.com",
        full_name="Test User",
        hashed_password=password_hash.hash(password)
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    response = client.post("/token", data={
        "username": user.username,
        "password": password
    })

    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_failure(client):
    response = client.post("/token", data={
        "username": "nonexistentuser",
        "password": "wrongpassword"
    })

    assert response.status_code == 401
    data = response.json()

    assert data["detail"] == "Incorrect username or password"