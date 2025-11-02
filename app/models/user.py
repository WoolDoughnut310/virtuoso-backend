from sqlmodel import SQLModel, Field

class UserBase(SQLModel):
    username: str = Field(index=True)
    email: str | None = None
    full_name: str | None = None
    is_artist: bool = Field(default=False)

class User(UserBase, table=True):
    __tablename__ = "users" # type: ignore
    id: int | None = Field(default=None, primary_key=True)
    hashed_password: str

class UserPublic(UserBase):
    id: int

class UserCreate(UserBase):
    password: str

class UserUpdate(SQLModel):
    username: str | None = None
    email: str | None = None
    full_name: str | None = None
    password: str | None = None