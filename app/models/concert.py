from datetime import datetime as dt, timedelta
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from pydantic import BaseModel

def three_days_from_now() -> dt:
    return dt.now() + timedelta(days=3)

if TYPE_CHECKING:
    from app.models.artist import Artist, ArtistPublic

class ImageUploadResponse(BaseModel):
    cover_image_url: str

class Song(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    file_url: str

    concert_id: int = Field(foreign_key="concert.id")
    concert: "Concert" = Relationship(back_populates="songs")

class ConcertBase(SQLModel):
    name: str = "Default Concert"
    start_time: dt = Field(default_factory=three_days_from_now)
    max_capacity: int = Field(default=5000)
    ticket_price: float = Field(default=0.0)
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
    start_time: dt | None = None
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