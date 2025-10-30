def test_login_success(client, make_test_user):
    password = "securepassword"
    user = make_test_user(password)

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