def test_register_user(client):
    response = client.post("/register", json={
        "username": "testuser",
        "email": "testuser@email.com",
        "full_name": "Test User",
        "password": "securepassword"
    })

    assert response.status_code == 200
    data = response.json()

    assert "password" not in data
    assert "id" in data