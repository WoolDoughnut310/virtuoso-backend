from app.config import settings
import cloudinary
from cloudinary.uploader import upload, upload_image

cloudinary.config(
    cloud_name=settings.cloudinary_cloud_name,
    api_key=settings.cloudinary_api_key,
    api_secret=settings.cloudinary_api_secret,
    secure=True,
)

audio_content_types = [
    "audio/mpeg",  # .mp3
    "audio/wav",  # .wav
    "audio/x-wav",  # sometimes used for .wav
    "audio/ogg",  # .ogg
    "audio/webm",  # .webm (Web Audio)
    "audio/aac",  # .aac
    "audio/mp4",  # .m4a, .mp4
    "audio/x-aiff",  # .aiff, .aif
    "audio/flac",  # .flac
    "audio/x-flac",  # legacy FLAC type
    "audio/3gpp",  # .3gp
    "audio/3gpp2",  # .3g2
]

image_content_types = ["image/jpeg", "image/png", "image/webp"]
