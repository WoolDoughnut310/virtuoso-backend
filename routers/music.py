from fastapi import APIRouter, UploadFile, Depends
import os
from uuid import uuid4
from dependencies import get_media_path

router = APIRouter()

@router.post("/upload")
async def upload_file(file: UploadFile, media_path: str = Depends(get_media_path)):
    os.makedirs(media_path, exist_ok=True)
    filename = f"{uuid4().hex}.bin"
    file_path = os.path.join(media_path, filename)

    with open(file_path, "wb") as out_file:
        for chunk in iter(lambda: file.file.read(1024 * 1024), b""):
            out_file.write(chunk)

    return {"filename": filename, "ok": True}
