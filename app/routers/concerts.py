from fastapi import APIRouter, UploadFile, HTTPException, Query
from app.models.concert import ConcertBase, ConcertPublic, Concert, Song, PaginatedConcerts
from app.dependencies.artists import CurrentArtistDep
from app.dependencies.db import SessionDep
from app.dependencies.concerts import ArtistConcertDep, ConcertDep
from app.concert_manager import ConcertManager
from sqlmodel import select, col, nulls_last
from app.dependencies.media import get_media_root
from typing import List, Literal
from uuid import uuid4
import os

concert_managers: dict[int, ConcertManager] = {}

def get_concert_manager(concert_id: int, db: SessionDep) -> ConcertManager:
    if concert_id not in concert_managers:
        concert_managers[concert_id] = ConcertManager(concert_id, db)
    return concert_managers[concert_id]

router = APIRouter(prefix="/concerts")

@router.post("/upload/{concert_id}")
async def upload_file(
    concert: ArtistConcertDep,
    file: UploadFile,
    session: SessionDep,
):
    assert concert.id is not None

    filename = file.filename
    if not filename:
        raise HTTPException(status_code=400, detail="No filename")

    # Create a folder for this concert using its ID
    media_root = get_media_root()
    media_dir = os.path.join(media_root, str(concert.id))
    os.makedirs(media_dir, exist_ok=True)

    # Generate a unique filename with the same extension
    ext = os.path.splitext(filename)[1].lower()
    new_filename = f"{uuid4().hex}{ext}"
    file_path = os.path.join(media_dir, new_filename)

    # Save the file
    with open(file_path, "wb") as out_file:
        for chunk in iter(lambda: file.file.read(1024 * 1024), b""):
            out_file.write(chunk)

    # Create song record
    song = Song(name=filename, file_path=file_path, concert_id=concert.id)
    session.add(song)
    session.commit()

    # Load track into the concert manager
    cm = get_concert_manager(concert.id, session)
    cm.load_track(song=song)

    return {"filename": new_filename, "ok": True}

@router.post("/start/{concert_id}")
async def start_concert(concert: ArtistConcertDep, session: SessionDep):
    assert concert.id is not None

    cm = get_concert_manager(concert.id, session)
    cm.start()
    return {"ok": True}


@router.post("/stop/{concert_id}")
async def stop_concert(concert: ArtistConcertDep):
    assert concert.id is not None

    cm = concert_managers.get(concert.id)
    if not cm:
        raise HTTPException(status_code=404, detail="Concert not found")
    cm.stop()
    return {"ok": True}


@router.post("/create", response_model=ConcertPublic)
async def create_concert(concert: ConcertBase, session: SessionDep, artist: CurrentArtistDep):
    assert artist.id is not None

    concert_db = Concert(**concert.model_dump(), artist_id=artist.id)
    session.add(concert_db)
    session.commit()
    session.refresh(concert_db)
    return concert_db

@router.get("/discover", response_model=PaginatedConcerts)
async def discover_concerts(
    session: SessionDep,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: Literal["upcoming", "popularity"] = Query("upcoming", description="Sort order"),
):
    query = select(Concert)

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