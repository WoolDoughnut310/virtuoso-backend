from aiortc.contrib.media import MediaPlayer
from aiortc import MediaStreamTrack, MediaStreamError
from av import AudioFrame
from app.dependencies.media import get_media_path
from fractions import Fraction
import numpy as np

class ConcertManager(MediaStreamTrack):
    kind = "audio"

    def __init__(self):
        self.file_dir = get_media_path()
        self._started = False

        self._tracks: list[MediaStreamTrack] = []
        self._track_ptr = -1
        self.load_tracks()
        self._track = self.next_track()

        self._sample_rate = 48000
        self._channels = 2
        self._samples = 960
    
    def next_track(self):
        self._track_ptr += 1
        if self._track_ptr < len(self._tracks):
            return self._tracks[self._track_ptr]
        else:
            self.stop()
            raise MediaStreamError("eof")
    
    def load_tracks(self):
        for file_path in self.file_dir.iterdir():
            player = MediaPlayer(file_path)
            self._tracks.append(player.audio) # type: ignore
    
    def start(self):
        self._started = True

    def stop(self):
        for t in self._tracks:
            t.stop()
            
    async def recv(self):
        if not self._started:
            frame = AudioFrame(format="s16", layout="stereo", samples=self._samples)
            frame.pts = 0
            frame.time_base = Fraction(1, self._sample_rate)
            silent_data = np.zeros((self._channels, self._samples), dtype=np.int16)
            frame.planes[0].update(silent_data.tobytes())
            return frame
        
        try:
            return await self._track.recv()
        except MediaStreamError:
            self._track = self.next_track()            
            return await self._track.recv()