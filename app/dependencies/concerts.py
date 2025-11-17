from fastapi import Depends, HTTPException, status
from sqlmodel import select
from app.models.concert import Concert
from app.dependencies.db import SessionDep
from app.dependencies.artists import CurrentArtistDep
from typing import Annotated
from app.concert_manager import ConcertManager

def get_concert(concert_id: int, session: SessionDep) -> Concert:
    concert = session.exec(
        select(Concert).where(Concert.id == concert_id)
    ).first()
    if not concert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Concert not found")
    return concert
ConcertDep = Annotated[Concert, Depends(get_concert)]

def get_artist_concert(concert: ConcertDep, artist: CurrentArtistDep) -> Concert:
    if concert.artist_id != artist.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to access this concert")

    return concert
ArtistConcertDep = Annotated[Concert, Depends(get_artist_concert)]


concert_managers: dict[int, ConcertManager] = {}

# Use the ConcertDep to ensure the concert exists
def get_concert_manager(concert: ConcertDep, session: SessionDep) -> ConcertManager:
    assert concert.id is not None
    if concert.id not in concert_managers:
        concert_managers[concert.id] = ConcertManager(concert.id, session)
    return concert_managers[concert.id]
ConcertManagerDep = Annotated[ConcertManager, Depends(get_concert_manager)]

def get_artist_concert_manager(concert_manager: ConcertManagerDep, artist: CurrentArtistDep) -> ConcertManager:
    if concert_manager.id != artist.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to access this concert manager")
    return concert_manager
ArtistConcertManagerDep = Annotated[ConcertManager, Depends(get_artist_concert_manager)]