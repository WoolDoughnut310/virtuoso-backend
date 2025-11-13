from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.artist import Artist, ArtistPublic


class Song(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    file_path: str

    concert_id: int = Field(foreign_key="concert.id")
    concert: "Concert" = Relationship(back_populates="songs")

class ConcertBase(SQLModel):
    name: str
    start_time: datetime
    max_capacity: int = Field(default=5000)
    ticket_price: float
    description: str = Field(default="")
    cover_image_url: Optional[str] = Field(default=None)

class Concert(ConcertBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    artist_id: int = Field(foreign_key="artist.id")
    artist: "Artist" = Relationship(back_populates="concerts")

    songs: List["Song"] = Relationship(back_populates="concert")
    popularity: int = Field(default=0)

class ConcertUpdate(SQLModel):
    name: str | None = None
    start_time: datetime | None = None
    max_capacity: int | None = None
    ticket_price: float | None = None
    description: str | None = None
    cover_image_url: str | None = None

class ConcertPublic(ConcertBase):
    id: int
    artist: "ArtistPublic"

class PaginatedConcerts(SQLModel):
    items: List[ConcertPublic]
    hasMore: bool

from app.models.artist import ArtistPublic
ConcertPublic.model_rebuild()