from aiortc.contrib.media import MediaPlayer, MediaRelay

class AudioManager:
    def __init__(self, file_path):
        self.relay = MediaRelay()
        self.file_path = file_path
        self.player = MediaPlayer(file_path)
        if self.player.audio:
            self.track = self.relay.subscribe(self.player.audio)

    async def loop_if_ended(self):
        if self.player.audio and self.player.audio.readyState == "ended":
            self.player = MediaPlayer(self.file_path)
            if self.player.audio:
                self.track = self.relay.subscribe(self.player.audio)