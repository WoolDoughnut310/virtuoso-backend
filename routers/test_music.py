from io import BytesIO
from main import app
from dependencies import get_current_user
import pytest

@pytest.fixture
def make_file_upload(client, make_test_user):
    def _make_file_upload(filename: str, content: bytes, is_artist: bool = True):
        user = make_test_user(is_artist=is_artist)
        app.dependency_overrides[get_current_user] = lambda: user

        data = {"file": (filename, BytesIO(content))}

        return client.post("/upload", files=data)
    
    return _make_file_upload

def test_upload_success(make_file_upload, media_path):
    file_content = b"hello world"
    response = make_file_upload("test.txt", file_content, is_artist=True)
    
    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert "filename" in response.json()

    uploaded_file = media_path / response.json()["filename"]
    assert uploaded_file.exists()
    assert uploaded_file.read_bytes() == file_content

def test_upload_unauthorized(make_file_upload):
    file_content = b"hello world"
    response = make_file_upload("test.txt", file_content, is_artist=False)
    
    assert response.status_code == 403