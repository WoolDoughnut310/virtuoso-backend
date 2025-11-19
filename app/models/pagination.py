from typing import TypeVar, Generic, List
from sqlmodel import SQLModel

T = TypeVar("T", bound=SQLModel)

class PaginatedResponse(SQLModel, Generic[T]):
    """
    A generic response model for paginated lists of any SQLModel type.
    """
    # The list of items, where T can be Concert, MediaAsset, etc.
    items: List[T]