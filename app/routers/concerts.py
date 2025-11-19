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
    PaginatedConcerts,
    ConcertUpdate,
    ConcertSetlistItemPublic,
    ConcertSetlistItem,
    ConcertSetlistItemCreate,
)
from app.dependencies.artists import CurrentArtistDep
from app.dependencies.db import SessionDep
from app.dependencies.concerts import (
    ArtistConcertDep,
    ConcertDep,
    ConcertManagerDep,
    ArtistConcertManagerDep,
)
from app.models.artist import MediaAsset
from aiortc import RTCPeerConnection
from app.concert_manager import Listener
from sqlmodel import select, col, nulls_last, Session
from app.models.concert import ImageUploadResponse
from app.dependencies.concerts import get_concert_manager, concert_managers
from typing import Literal, Optional
from contextlib import asynccontextmanager
from app.database import engine
from app.storage import upload_image, image_content_types


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

    if file.content_type not in image_content_types:
        raise HTTPException(status_code=400, detail="Invalid image format.")

    file_bytes = await file.read()

    image_result = upload_image(file_bytes)

    return {"cover_image_url": image_result.url}


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
    concert: ArtistConcertDep,
    data: ConcertUpdate,
    session: SessionDep,
    concert_manager: ArtistConcertManagerDep,
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


@router.post("/{concert_id}/setlist", response_model=ConcertSetlistItemPublic)
async def create_setlist_item(
    item_data: ConcertSetlistItemCreate,
    artist: CurrentArtistDep,
    concert: ArtistConcertDep,
    session: SessionDep,
):
    item_db = ConcertSetlistItem.model_validate(
        item_data, update={"concert_id": concert.id}
    )

    # Check if artist owns the asset referenced in the request
    session.exec(
        select(MediaAsset)
        .where(MediaAsset.artist_id == artist.id)
        .where(MediaAsset.id == item_db.asset_id)
    )

    session.add(item_db)
    session.commit()
    session.refresh(item_db)

    return item_db


@router.delete(
    "/{concert_id}/setlist/{item_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_setlist_item(
    concert: ArtistConcertDep, item_id: int, session: SessionDep
):
    setlist_item = session.exec(
        select(ConcertSetlistItem)
        .where(ConcertSetlistItem.id == item_id)
        .where(ConcertSetlistItem.concert_id == concert.id)
    )
    session.delete(setlist_item)
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
