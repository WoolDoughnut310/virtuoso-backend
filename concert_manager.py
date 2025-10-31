from aiortc.contrib.media import MediaPlayer, MediaRelay
from aiortc import MediaStreamTrack, MediaStreamError
from dependencies import get_media_path
import asyncio

class ConcertTrack(MediaStreamTrack):
    kind = "audio"

    def __init__(self, manager: ConcertManager):
        super().__init__()
        self._manager = manager
        self._track: MediaStreamTrack = self._manager.next_track() # type: ignore
        self._last = None

    async def recv(self):
        while True:
            if not self._manager._started:
                await asyncio.sleep(0.02)
                if self._last is not None:
                    return self._last
            
            try:
                frame = await self._track.recv()
                self._last = frame
                return frame
            except MediaStreamError:
                next_track = self._manager.next_track()
                if next_track is None:
                    self.stop()
                    raise MediaStreamError
                self._track = next_track

class ConcertManager:
    def __init__(self):
        self.file_dir = get_media_path()
        
        self._relay = MediaRelay()
        self._started = False

        self._tracks: list[MediaStreamTrack] = []
        self.load_tracks()
        self.track_ptr = -1
    
    def next_track(self):
        self.track_ptr += 1
        if self.track_ptr < len(self._tracks):
            return self._tracks[self.track_ptr]
        return None
    
    def load_tracks(self):
        for file_path in self.file_dir.iterdir():
            player = MediaPlayer(file_path)
            self._tracks.append(player.audio) # type: ignore
    
    def start(self):
        self._started = True

    def stop(self):
        for t in self._tracks:
            t.stop()
    
    def create_track(self):
        return self._relay.subscribe(ConcertTrack(self))