from app.concert_manager import ConcertManager
from typing import Annotated
from fastapi import Depends

_concert_manager: ConcertManager | None = None

def set_concert_manager(manager: ConcertManager):
    global _concert_manager
    _concert_manager = manager

def get_concert_manager() -> ConcertManager:
    if _concert_manager is None:
        raise RuntimeError("ConcertManager not initialized")
    return _concert_manager


ConcertManagerDep = Annotated[ConcertManager, Depends(get_concert_manager)]