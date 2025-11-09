from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.concert import Concert

class ArtistBase(SQLModel):
    name: str

class Artist(ArtistBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user: "User" = Relationship(back_populates="artist")
    concerts: List["Concert"] = Relationship(back_populates="artist")

class ArtistPublic(ArtistBase):
    id: int