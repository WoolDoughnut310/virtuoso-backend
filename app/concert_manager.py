from aiortc.contrib.media import MediaPlayer, MediaRelay
from aiortc import MediaStreamTrack, MediaStreamError
from av import AudioFrame
from app.models.concert import Song
from fractions import Fraction
from sqlmodel import Session, select
import numpy as np
from datetime import datetime as dt
from app.dependencies.scheduler import get_scheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.job import Job
from apscheduler.jobstores.base import JobLookupError

class ConcertManager:
    def __init__(self, id: int, db: Session):
        self._relay = MediaRelay()
        self._started = False
        self.id = id
        self.db = db
        self._concert_track = ConcertTrack(self)
        
        self.load_tracks = self._concert_track.load_tracks
        self.load_track = self._concert_track.load_track

        self.load_tracks()
        self._start_job: Job | None = None
    
    def create_track(self):
        return self._relay.subscribe(self._concert_track)
    
    def start(self):
        self._started = True
    
    def stop(self):
        self._concert_track.stop()
        self._started = False
        if self._start_job:
            try:
                self._start_job.remove()
            except JobLookupError:
                pass
    
    def schedule_start(self, when: dt):
        scheduler = get_scheduler()
        if self._start_job:
            try:
                self._start_job.remove()
            except JobLookupError:
                pass
        self._start_job = scheduler.add_job(self.start, DateTrigger(run_date=when))

class ConcertTrack(MediaStreamTrack):
    kind = "audio"

    def __init__(self, manager: ConcertManager):
        super().__init__()
        self.manager = manager

        self._tracks: list[MediaStreamTrack] = []
        self._track_ptr = -1
        self._track: MediaStreamTrack | None = None

        self._file_urls = {}

        self._sample_rate = 48000
        self._channels = 2
        self._samples = 960
        self._pts = 0

    def get_track(self):
        return self._tracks[self._track_ptr]

    
    def next_track(self):
        self._track_ptr += 1
        if self._track_ptr < len(self._tracks):
            return self.get_track()
        else:
            self.stop()
            raise MediaStreamError("eof")
    
    def load_track(self, song_id: int = -1, song: Song | None = None):
        if song_id != -1:
            song = self.manager.db.exec(select(Song).where(Song.id == song_id)).first()

        if not song:
            raise Exception("Song not found")
        
        if song.file_url in self._file_urls:
            return
        
        self._file_urls[song.file_url] = True
        player = MediaPlayer(song.file_url)
        if player.audio:
            self._tracks.append(player.audio)
    
    def load_tracks(self):
        songs = self.manager.db.exec(select(Song).where(Song.id == self.manager.id)).all()

        for song in songs:
            self.load_track(song=song)

    def stop(self):
        for t in self._tracks:
            t.stop()
            
    async def recv(self):
        if not self.manager._started:
            print("silencing...")
            frame = AudioFrame(format="s16", layout="stereo", samples=self._samples)
            frame.pts = self._pts
            self._pts += self._samples
            frame.time_base = Fraction(1, self._sample_rate)
            silent_data = np.zeros((self._channels, self._samples), dtype=np.int16)
            frame.planes[0].update(silent_data.tobytes())
            return frame
        
        try:
            if self._track is None:
                self._track = self.next_track()
            return await self._track.recv()
        except MediaStreamError:
            self._track = self.next_track()
            return await self._track.recv()