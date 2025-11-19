from datetime import datetime as dt, timedelta
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship, UniqueConstraint
from pydantic import BaseModel
from app.models.pagination import PaginatedResponse


def three_days_from_now() -> dt:
    return dt.now() + timedelta(days=3)


if TYPE_CHECKING:
    from app.models.artist import Artist, ArtistPublic, MediaAsset, MediaAssetPublic


class ImageUploadResponse(BaseModel):
    cover_image_url: str


class ConcertSetlistItemBase(SQLModel):
    name: str
    track_number: int = Field(index=True)


class ConcertSetlistItem(ConcertSetlistItemBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    asset_id: int = Field(foreign_key="mediaasset.id")
    asset: "MediaAsset" = Relationship(back_populates="setlist_references")

    concert_id: int = Field(foreign_key="concert.id")
    concert: "Concert" = Relationship(back_populates="setlist_items")

    __table_args__ = (
        UniqueConstraint("concert_id", "track_number", name="unique_concert_track"),
    )


class ConcertSetlistItemPublic(ConcertSetlistItemBase):
    id: int
    asset: "MediaAssetPublic"


class ConcertSetlistItemCreate(ConcertSetlistItemBase):
    pass


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

    setlist_items: List["ConcertSetlistItem"] = Relationship(back_populates="concert")
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
    setlist_items: List["ConcertSetlistItemPublic"]


class PaginatedConcerts(PaginatedResponse[ConcertPublic]):
    pass


from app.models.artist import ArtistPublic

ConcertPublic.model_rebuild()
