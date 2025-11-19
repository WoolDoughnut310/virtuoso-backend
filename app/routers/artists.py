from fastapi import APIRouter, UploadFile, HTTPException, Query, status
from app.models.artist import MediaAsset, PaginatedMediaAssets, MediaAssetPublic
from app.dependencies.artists import CurrentArtistDep
from app.dependencies.db import SessionDep
from app.storage import upload, audio_content_types
from sqlmodel import select

router = APIRouter(prefix="/artists")


@router.get("/media", response_model=PaginatedMediaAssets)
async def list_media(
    artist: CurrentArtistDep,
    session: SessionDep,
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    assert artist.id is not None

    assets = session.exec(
        select(MediaAsset)
        .where(MediaAsset.artist_id == artist.id)
        .offset(offset)
        .limit(limit + 1)
    ).all()

    has_more = len(assets) > limit
    items = assets[:limit]

    return {"items": items, "hasMore": has_more}


@router.post("/media", response_model=MediaAssetPublic)
async def upload_media(file: UploadFile, session: SessionDep, artist: CurrentArtistDep):
    assert artist.id is not None

    if file.content_type not in audio_content_types:
        raise HTTPException(status_code=400, detail="Invalid audio format.")

    content = await file.read()
    result = upload(content, resource_type="video")

    audio_data = result["audio"]

    asset = MediaAsset(
        url=result["url"],
        artist_id=artist.id,
        duration=result["duration"],
        codec=audio_data["codec"],
        bit_rate=result["bit_rate"],
        frequency=audio_data["frequency"],
        channels=audio_data["channels"],
        channel_layout=audio_data["channel_layout"],
    )
    session.add(asset)
    session.commit()

    return asset


@router.delete("/media/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_media(asset_id: int, session: SessionDep, artist: CurrentArtistDep):
    asset = session.exec(
        select(MediaAsset)
        .where(MediaAsset.artist_id == artist.id)
        .where(MediaAsset.id == asset_id)
    ).first()
    session.delete(asset)
    session.commit()
    return
