from fastapi import APIRouter, UploadFile, Depends
import os
from uuid import uuid4
from dependencies.media import MediaPathDep
from dependencies.artists import check_artist
from dependencies.concerts import ConcertManagerDep

router = APIRouter(dependencies=[Depends(check_artist)])

@router.post("/upload")
async def upload_file(file: UploadFile, media_path: MediaPathDep):
    media_path.mkdir(exist_ok=True)
    filename = f"{uuid4().hex}.bin"
    file_path = os.path.join(media_path, filename)

    with open(file_path, "wb") as out_file:
        for chunk in iter(lambda: file.file.read(1024 * 1024), b""):
            out_file.write(chunk)

    return {"filename": filename, "ok": True}

@router.post("/start")
async def start_concert(concert_manager: ConcertManagerDep):

    return {"ok": True}