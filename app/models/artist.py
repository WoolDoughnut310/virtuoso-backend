from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from app.models.pagination import PaginatedResponse

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.concert import Concert, ConcertSetlistItem

class ArtistBase(SQLModel):
    name: str

class Artist(ArtistBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user: "User" = Relationship(back_populates="artist")
    concerts: List["Concert"] = Relationship(back_populates="artist")
    assets: List["MediaAsset"] = Relationship(back_populates="artist")

class ArtistPublic(ArtistBase):
    id: int

class MediaAssetBase(SQLModel):
    duration: int
    codec: str

class MediaAsset(MediaAssetBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str
    bit_rate: int
    frequency: int
    channels: int
    channel_layout: Optional[str] = None

    setlist_references: List["ConcertSetlistItem"] = Relationship(back_populates="asset")

    artist_id: int = Field(foreign_key="artist.id")
    artist: "Artist" = Relationship(back_populates="assets")

class MediaAssetPublic(MediaAssetBase):
    id: int

class PaginatedMediaAssets(PaginatedResponse[MediaAssetPublic]):
    pass