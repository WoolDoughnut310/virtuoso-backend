from fastapi import Depends, HTTPException, status
from sqlmodel import select
from app.models.concert import Concert
from app.dependencies.db import SessionDep
from app.dependencies.artists import CurrentArtistDep
from typing import Annotated

def get_concert(concert_id: int, session: SessionDep) -> Concert:
    concert = session.exec(
        select(Concert).where(Concert.id == concert_id)
    ).first()
    if not concert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Concert not found")
    return concert

def get_artist_concert(concert_id: int, session: SessionDep, artist: CurrentArtistDep) -> Concert:
    concert = get_concert(concert_id, session)

    if concert.artist_id != artist.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to access this concert")

    return concert

ConcertDep = Annotated[Concert, Depends(get_concert)]
ArtistConcertDep = Annotated[Concert, Depends(get_artist_concert)]