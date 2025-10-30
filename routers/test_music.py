from fastapi.testclient import TestClient
from io import BytesIO
from dependencies import get_media_path
from main import app

def test_upload(client, tmp_path):
    media_path = tmp_path / "media"

    file_content = b"hello world"

    app.dependency_overrides[get_media_path] = lambda: str(media_path)
    data = {"file": ("test.txt", BytesIO(file_content))}

    response = client.post("/upload", files=data)
    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert "filename" in response.json()

    uploaded_file = media_path / response.json()["filename"]
    assert uploaded_file.exists()
    assert uploaded_file.read_bytes() == file_content