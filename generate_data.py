from app.dependencies.db import get_session
from faker import Faker
from app.models.artist import *
from app.models.concert import *
from app.models.user import *
from app.routers.authentication import password_hash
from app.routers.artists import upload_media
from fastapi import UploadFile
import random
import numpy as np
from synthesizer import Synthesizer, Waveform
from scipy.io.wavfile import write as write_wav
from sqlmodel import select
import io

session = next(get_session())
fake = Faker()

NOTE_FREQUENCIES = [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88]  # C4-B4

def generate_audio_file(duration_sec=5, sample_rate=22050) -> UploadFile:
    """
    Generate a musical audio file using synthesizer and return a FastAPI UploadFile.
    """
    NOTE_FREQUENCIES = [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88]

    synth = Synthesizer(osc1_waveform=Waveform.sine, osc1_volume=0.3,
                        osc2_waveform=Waveform.square, osc2_volume=0.2)

    total_samples = int(duration_sec * sample_rate)
    audio = np.zeros(total_samples, dtype=np.float32)

    for _ in range(random.randint(5, 12)):
        freq = random.choice(NOTE_FREQUENCIES)
        start_time = random.uniform(0, duration_sec * 0.8)
        note_duration = random.uniform(0.3, 1.0)

        # Convert times to sample indices
        start_idx = int(start_time * sample_rate)
        end_idx = int(min((start_time + note_duration) * sample_rate, total_samples))
        actual_duration_sec = (end_idx - start_idx) / sample_rate

        # Generate waveform for the note (duration in seconds)
        note_wave = synth.generate_constant_wave(freq, actual_duration_sec)

        # Make sure note_wave length matches slice length
        note_wave = note_wave[:end_idx - start_idx]

        # Add to main audio
        audio[start_idx:end_idx] += note_wave

    # Normalize audio to -1..1
    audio = np.clip(audio, -1.0, 1.0)

    # Convert to 16-bit PCM
    audio_int16 = np.int16(audio * 32767)

    # Write WAV to BytesIO
    audio_bytes = io.BytesIO()
    write_wav(audio_bytes, sample_rate, audio_int16)
    audio_bytes.seek(0)

    filename = f"{fake.word()}.wav"
    return UploadFile(filename=filename, file=audio_bytes)

async def generate_user(password=None):
    plain_password = password or fake.password()
    user = User(
        username=fake.user_name(),
        hashed_password=password_hash.hash(plain_password),
        email=fake.email(),
        full_name=fake.name()
    )
    session.add(user)
    session.commit()
    return user, plain_password

async def generate_artist(user: User):
    artist = Artist(
        name=f"{fake.word().title()} {fake.word().title()}",
        user=user
    )
    session.add(artist)
    session.commit()
    return artist

async def generate_concert(artist: Artist):
    assert artist.id is not None
    concert = Concert(
        name=fake.catch_phrase().title(),
        start_time=fake.date_time(),
        max_capacity=fake.random_int(min=5, max=10000),
        ticket_price=fake.pyfloat(min_value=5, max_value=500, right_digits=2),
        artist_id=artist.id,
        description=fake.text(),
        artist=artist
    )
    session.add(concert)
    session.commit()
    return concert

async def generate_asset(artist: Artist):
    file = generate_audio_file()
    asset = await upload_media(file, session, artist)
    return asset

async def generate_song(asset: MediaAsset, concert: Concert, existing_tracks: int):
    assert concert.id is not None
    assert asset.id is not None

    setlist_item = ConcertSetlistItem(
        name=" ".join(fake.words()),
        concert_id=concert.id,
        asset_id=asset.id,
        track_number=existing_tracks + 1
    )
    session.add(setlist_item)
    session.commit()
    return setlist_item

async def generate_demo_data(
    min_users=1, max_users=5,
    min_concerts=1, max_concerts=3,
    min_songs=1, max_songs=5,
    artist_probability=0.7  # proportion of users who get an artist
):
    num_users = fake.random_int(min=min_users, max=max_users)

    for _ in range(num_users):
        user, plain_password = await generate_user()
        print(f"[USER] {user.username} | {user.email} | password: {plain_password}")

        # Decide if this user gets an artist
        if random.random() < artist_probability:
            artist = await generate_artist(user)
            print(f"  -> ARTIST: {artist.name}")

            num_concerts = fake.random_int(min=min_concerts, max=max_concerts)
            for _ in range(num_concerts):
                concert = await generate_concert(artist)

                num_songs = fake.random_int(min=min_songs, max=max_songs)
                for existing_tracks in range(num_songs):
                    asset = await generate_asset(artist)
                    await generate_song(asset, concert, existing_tracks)
        else:
            # User exists without an artist
            continue

# Run the async generation
if __name__ == "__main__":
    import asyncio
    # asyncio.run(generate_demo_data())

def prop_concert(id: int):
    import requests
    response = requests.patch(f"http://localhost:8000/concerts/{id}", json={
        "start_time": (dt.now() + timedelta(seconds=20)).isoformat()
    })
    print(f"OK: {response.ok}")
    import webbrowser
    webbrowser.open(f"http://localhost:5173/concert/{id}/live")