from fastapi import Depends
from typing import Annotated
from pathlib import Path

audio_content_types = [
    "audio/mpeg",      # .mp3
    "audio/wav",       # .wav
    "audio/x-wav",     # sometimes used for .wav
    "audio/ogg",       # .ogg
    "audio/webm",      # .webm (Web Audio)
    "audio/aac",       # .aac
    "audio/mp4",       # .m4a, .mp4
    "audio/x-aiff",    # .aiff, .aif
    "audio/flac",      # .flac
    "audio/x-flac",    # legacy FLAC type
    "audio/3gpp",      # .3gp
    "audio/3gpp2",     # .3g2
]

def get_media_root():
    return Path("app/media")

MediaRootDep = Annotated[Path, Depends(get_media_root)]