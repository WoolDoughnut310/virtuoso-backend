from app.concert_manager import ConcertManager
from typing import Annotated
from fastapi import Depends

concert_manager = ConcertManager()

def get_concert_manager():
    return concert_manager

ConcertManagerDep = Annotated[ConcertManager, Depends(get_concert_manager)]