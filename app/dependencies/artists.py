from fastapi import HTTPException, status, Depends
from app.dependencies.users import CurrentUserDep
from typing import Annotated
from app.models.artist import Artist

def get_current_artist(user: CurrentUserDep):
    if user.artist == None or user.artist.id == None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not an artist.")
    return user.artist

CurrentArtistDep = Annotated[Artist, Depends(get_current_artist)]