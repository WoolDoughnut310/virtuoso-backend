import asyncio
from aiortc import MediaStreamTrack, RTCPeerConnection
from aiortc.contrib.media import MediaPlayer, MediaRelay
from app.dependencies.db import SessionDep
from app.models.concert import ConcertSetlistItem, Concert
from app.models.artist import MediaAsset
from sqlmodel import select, col
from apscheduler.triggers.date import DateTrigger
from fastapi import WebSocket
from fastapi.websockets import WebSocketState
from app.dependencies.scheduler import get_scheduler
from apscheduler.job import Job
from apscheduler.jobstores.base import JobLookupError
from typing import TypedDict, Dict
from uuid import uuid4
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.sdp import candidate_from_sdp
import subprocess
import asyncio
import os, tempfile


class Listener(TypedDict):
    pc: RTCPeerConnection
    ws: WebSocket


def merge_audio_tracks(files: list[str]):
    temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    ffmpeg_cmd = ["ffmpeg"]
    for f in files:
        ffmpeg_cmd.extend(["-i", f])
    ffmpeg_cmd.extend(
        [
            "-filter_complex",
            f"concat=n={len(files)}:v=0:a=1[outa]",
            "-map",
            "[outa]",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-c:a",
            "pcm_s16le",
            temp_file,
            "-y",
        ]
    )
    subprocess.run(
        ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
    )
    return temp_file


class ConcertManager:
    def __init__(self, id: int, session: SessionDep):
        self.id = id
        self.listeners: Dict[str, Listener] = {}
        self.session = session
        self.playlist_track: MediaStreamTrack | None = None
        self.start_job: Job | None = None
        self._dummy_task: asyncio.Task | None = None
        self._temp_file: str | None = None
        self.relay = MediaRelay()

    async def _consume_dummy(self):
        if not self.playlist_track:
            return
        dummy_track = self.relay.subscribe(self.playlist_track)
        while True:
            try:
                await dummy_track.recv()
            except Exception:
                break  # Track ended

    def start(self):
        from app.main import MAIN_LOOP

        if MAIN_LOOP is None:
            raise RuntimeError("Main loop not initialized yet")

        asyncio.run_coroutine_threadsafe(self._start_async(), MAIN_LOOP)

    async def _start_async(self):
        print("Starting playlist")
        playlist = self.session.exec(
            select(MediaAsset.url)
            .join(ConcertSetlistItem)
            .where(ConcertSetlistItem.concert_id == self.id)
            .order_by(col(ConcertSetlistItem.track_number))
        ).all()

        self._temp_file = merge_audio_tracks(list(playlist))
        self.playlist_track = MediaPlayer(self._temp_file).audio

        if self._dummy_task is None:
            self._dummy_task = asyncio.create_task(self._consume_dummy())

        for listener_id, listener in list(self.listeners.items()):
            self.add_track_to_listener(listener_id)

            try:
                await listener["ws"].send_json({"type": "renegotiate"})
            except Exception as e:
                print("Failed to send renegotiate to listener", listener_id, e)

    async def stop(self):
        if self._dummy_task:
            self._dummy_task.cancel()
            try:
                await self._dummy_task
            except asyncio.CancelledError:
                pass
            self._dummy_task = None
        if self.playlist_track:
            self.playlist_track.stop()
        self.remove_schedule_start()
        for listener_id in self.listeners.keys():
            await self.remove_listener(listener_id)
        if self._temp_file and os.path.exists(self._temp_file):
            os.remove(self._temp_file)

    def schedule_start(self):
        start_time = self.session.exec(
            select(Concert.start_time).where(Concert.id == self.id)
        ).first()
        if start_time is None:
            print("No start time set.")
            return

        scheduler = get_scheduler()
        self.remove_schedule_start()
        self.start_job = scheduler.add_job(self.start, DateTrigger(run_date=start_time))

    def remove_schedule_start(self):
        if self.start_job is None:
            return

        try:
            self.start_job.remove()
        except JobLookupError:
            pass

    def add_pc_handlers(self, listener_id: str):
        listener = self.listeners[listener_id]
        pc = listener["pc"]
        ws = listener["ws"]

        async def on_state_change():
            if pc.connectionState in ("failed", "closed", "disconnected"):
                await self.remove_listener(listener_id)

        async def on_icecandidate(candidate):
            if candidate is None:
                return
            await ws.send_json(
                {
                    "type": "candidate",
                    "candidate": candidate.candidate,
                    "sdpMid": candidate.sdpMid,
                    "sdpMLineIndex": candidate.sdpMLineIndex,
                }
            )

        pc.on("connectionstatechange", on_state_change)
        pc.on("icecandidate", on_icecandidate)

    def add_track_to_listener(self, listener_id: str):
        listener = self.listeners[listener_id]

        try:
            listener["pc"].addTrack(self.relay.subscribe(self.playlist_track))  # type: ignore
        except Exception as e:
            print("Failed to add track to listener", listener_id, e)

    async def add_listener(self, listener: Listener):
        await listener["ws"].accept()

        listener_id = str(uuid4())
        self.listeners[listener_id] = listener

        if self.playlist_track:
            self.add_track_to_listener(listener_id)

        self.add_pc_handlers(listener_id)

        return listener_id

    async def remove_listener(self, listener_id: str):
        if listener_id not in self.listeners:
            return
        listener = self.listeners.pop(listener_id)

        if listener["ws"].application_state == WebSocketState.DISCONNECTED:
            await listener["ws"].close()

        await listener["pc"].close()

    async def send_reaction(self, emoji: str, from_: str):
        for listener_id, listener in self.listeners.items():
            if listener_id == from_:
                continue
            await listener["ws"].send_json(
                {
                    "type": "emoji",
                    "emoji": emoji,
                }
            )

    async def receive_offer(self, listener_id: str, data):
        listener = self.listeners[listener_id]
        pc = listener["pc"]
        ws = listener["ws"]

        offer = RTCSessionDescription(sdp=data["sdp"], type="offer")
        await pc.setRemoteDescription(offer)
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        await ws.send_json(
            {
                "type": "answer",
                "sdp": pc.localDescription.sdp,
            }
        )

    async def receive_candidate(self, listener_id: str, data):
        listener = self.listeners[listener_id]
        pc = listener["pc"]

        cand = data["candidate"]
        candidate = candidate_from_sdp(cand["candidate"])
        candidate.sdpMid = cand.get("sdpMid")
        candidate.sdpMLineIndex = cand.get("sdpMLineIndex")
        await pc.addIceCandidate(candidate)
