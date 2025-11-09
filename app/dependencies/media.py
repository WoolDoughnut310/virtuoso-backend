from fastapi import Depends
from typing import Annotated
from pathlib import Path

def get_media_root():
    return Path("app/media")

MediaRootDep = Annotated[Path, Depends(get_media_root)]