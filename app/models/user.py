from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.artist import Artist

class UserBase(SQLModel):
    username: str = Field(index=True)
    email: str | None = None
    full_name: str | None = None


class User(UserBase, table=True):
    __tablename__ = "users" # type: ignore
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str

    artist_id: Optional[int] = Field(default=None, foreign_key="artist.id")
    artist: Optional["Artist"] = Relationship(back_populates="user")

class UserPublic(UserBase):
    id: int

class UserCreate(UserBase):
    password: str

class UserUpdate(SQLModel):
    username: str | None = None
    email: str | None = None
    full_name: str | None = None
    password: str | None = None