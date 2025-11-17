from fastapi import (
    APIRouter,
    UploadFile,
    HTTPException,
    Query,
    FastAPI,
    BackgroundTasks,
    status,
    WebSocket,
    WebSocketDisconnect,
)
from app.models.concert import (
    ConcertPublic,
    Concert,
    Song,
    PaginatedConcerts,
    ConcertUpdate,
)
from app.dependencies.artists import CurrentArtistDep
from app.dependencies.db import SessionDep
from app.dependencies.concerts import (
    ArtistConcertDep,
    ConcertDep,
    ConcertManagerDep,
    ArtistConcertManagerDep,
)
from aiortc import RTCPeerConnection
from app.concert_manager import Listener
from sqlmodel import select, col, nulls_last, Session
from app.dependencies.media import get_media_root, audio_content_types
from app.models.concert import ImageUploadResponse
from app.dependencies.concerts import get_concert_manager, concert_managers
from typing import Literal, Optional
from uuid import uuid4
from contextlib import asynccontextmanager
from app.database import engine
import os
from app.config import settings
from cloudinary.uploader import upload_image
import cloudinary

cloudinary.config(
    cloud_name=settings.cloudinary_cloud_name,
    api_key=settings.cloudinary_api_key,
    api_secret=settings.cloudinary_api_secret,
    secure=True,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    with Session(engine) as session:
        concerts = session.exec(select(Concert)).all()

        for concert in concerts:
            concert_manager = get_concert_manager(concert, session)
            concert_manager.schedule_start()
    yield
    for concert_manager in concert_managers.values():
        await concert_manager.stop()


router = APIRouter(prefix="/concerts", lifespan=lifespan)


@router.post("/upload-image/{concert_id}", response_model=ImageUploadResponse)
async def upload_concert_image(concert: ConcertDep, file: UploadFile):
    assert concert.id is not None

    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(status_code=400, detail="Invalid image format.")

    file_bytes = await file.read()

    image_result = upload_image(file_bytes)

    return {"cover_image_url": image_result.url}


@router.post("/upload-song/{concert_id}")
async def upload_song(
    concert: ArtistConcertDep,
    file: UploadFile,
    session: SessionDep,
):
    assert concert.id is not None

    filename = file.filename
    if not filename:
        raise HTTPException(status_code=400, detail="No filename")

    if file.content_type not in audio_content_types:
        raise HTTPException(status_code=400, detail="Invalid audio format.")

    # Create a folder for this concert using its ID
    media_root = get_media_root()
    media_dir = os.path.join(media_root, str(concert.id))
    os.makedirs(media_dir, exist_ok=True)

    # Generate a unique filename with the same extension
    ext = os.path.splitext(filename)[1].lower()
    new_filename = f"{uuid4().hex}{ext}"
    file_url = os.path.join(media_dir, new_filename)

    # Save the file
    with open(file_url, "wb") as out_file:
        for chunk in iter(lambda: file.file.read(1024 * 1024), b""):
            out_file.write(chunk)

    # Create song record
    song = Song(name=filename, file_url=file_url, concert_id=concert.id)
    session.add(song)
    session.commit()

    return {"filename": new_filename, "ok": True}


@router.post("/create", response_model=ConcertPublic)
async def create_concert(
    session: SessionDep, artist: CurrentArtistDep, background_tasks: BackgroundTasks
):
    assert artist.id is not None

    concert_db = Concert(artist_id=artist.id)
    session.add(concert_db)
    session.commit()
    session.refresh(concert_db)
    assert concert_db.id is not None

    def schedule_start(concert_id: int):
        with Session(engine) as s:
            concert = s.get(Concert, concert_id)
            if concert:
                concert_manager = get_concert_manager(concert, s)
                concert_manager.schedule_start()

    background_tasks.add_task(schedule_start, concert_db.id)

    return concert_db


@router.get("/discover", response_model=PaginatedConcerts)
async def discover_concerts(
    session: SessionDep,
    q: Optional[str] = None,
    artist_id: Optional[int] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: Literal["upcoming", "popularity"] = Query(
        "upcoming", description="Sort order"
    ),
):
    query = select(Concert)

    if q:
        like_expr = f"%{q}%"
        query = query.where(
            (col(Concert.name).ilike(like_expr))
            | (col(Concert.description).ilike(like_expr))
        )

    if artist_id:
        query = query.where(Concert.artist_id == artist_id)

    if min_price is not None:
        query = query.where(Concert.ticket_price >= min_price)

    if max_price is not None:
        query = query.where(Concert.ticket_price <= max_price)

    sort_columns = {
        "upcoming": nulls_last(col(Concert.start_time).asc()),
        "popularity": col(Concert.popularity).desc(),
    }

    query = query.order_by(sort_columns[sort_by])

    concerts = session.exec(query.offset(offset).limit(limit + 1)).all()

    has_more = len(concerts) > limit
    items = concerts[:limit]

    return {"items": items, "hasMore": has_more}


@router.get("/{concert_id}", response_model=ConcertPublic)
async def get_concert(concert: ConcertDep, session: SessionDep):
    concert.popularity += 1
    session.commit()
    return concert


@router.patch("/{concert_id}", response_model=ConcertPublic)
async def update_concert(
    concert: ConcertDep,
    data: ConcertUpdate,
    session: SessionDep,
    concert_manager: ConcertManagerDep, # change back to artist's
):
    assert concert.id is not None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(concert, key, value)

    session.add(concert)
    session.commit()
    session.refresh(concert)

    if data.start_time:
        concert_manager.schedule_start()

    return concert


@router.delete("/{concert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_concert(
    concert_manager: ArtistConcertManagerDep,
    concert: ArtistConcertDep,
    session: SessionDep,
):
    await concert_manager.stop()
    session.delete(concert)
    session.commit()
    return


@router.websocket("/{concert_id}")
async def live(ws: WebSocket, concert_manager: ConcertManagerDep):
    pc = RTCPeerConnection()

    listener: Listener = {
        "pc": pc,
        "ws": ws,
    }

    listener_id = await concert_manager.add_listener(listener)

    try:
        while True:
            data = await ws.receive_json()
            t = data["type"]

            if t == "offer":
                await concert_manager.receive_offer(listener_id, data)
            elif t == "candidate":
                await concert_manager.receive_candidate(listener_id, data)
            elif t == "emoji":
                await concert_manager.send_reaction(data.get("emoji"), listener_id)
    except WebSocketDisconnect:
        await concert_manager.remove_listener(listener_id)
