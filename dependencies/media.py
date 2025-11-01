from fastapi import Depends
from typing import Annotated
from pathlib import Path

def get_media_path():
    return Path("media")

MediaPathDep = Annotated[Path, Depends(get_media_path)]