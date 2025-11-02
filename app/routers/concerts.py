from fastapi import FastAPI, APIRouter, UploadFile, Depends
from uuid import uuid4
from app.dependencies.media import MediaPathDep
from app.dependencies.artists import check_artist
from app.concert_manager import ConcertManager
import os
from app.dependencies.concerts import set_concert_manager, ConcertManagerDep
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    manager = ConcertManager()
    set_concert_manager(manager)
    yield
    manager.stop()

# router = APIRouter(prefix="/concerts", lifespan=lifespan, dependencies=[Depends(check_artist)])
router = APIRouter(prefix="/concerts", lifespan=lifespan)

# @router.post("/upload")
@router.post("/upload", dependencies=[Depends(check_artist)])
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
    concert_manager.start()
    return {"ok": True}