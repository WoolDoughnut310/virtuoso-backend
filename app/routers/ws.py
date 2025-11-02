from fastapi import FastAPI, APIRouter, WebSocket
from aiortc import RTCPeerConnection, RTCSessionDescription
import asyncio, json
from aiortc.sdp import candidate_from_sdp
from app.dependencies.concerts import get_concert_manager, ConcertManagerDep
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await asyncio.gather(*[pc.close() for pc in pcs], return_exceptions=True)
    get_concert_manager().stop()


pcs = set()

router = APIRouter(lifespan=lifespan)

@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket, concert_manager: ConcertManagerDep):
    await ws.accept()
    pc = RTCPeerConnection()
    pcs.add(pc)

    pc.addTrack(concert_manager.create_track())

    @pc.on("icecandidate")
    async def on_icecandidate(candidate):
        if candidate:
            await ws.send_json({"type": "ice", "candidate": candidate.to_json()})

    while True:
        msg = json.loads(await ws.receive_text())
        if msg["type"] == "offer":
            offer = RTCSessionDescription(sdp=msg["sdp"], type="offer")
            await pc.setRemoteDescription(offer)

            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)
            await ws.send_json({"type": "answer", "sdp": pc.localDescription.sdp})
        elif msg["type"] == "ice":
            candidate = candidate_from_sdp(msg["candidate"]["candidate"])
            candidate.sdpMid = msg["candidate"]["sdpMid"]
            candidate.sdpMLineIndex = msg["candidate"]["sdpMLineIndex"]
            await pc.addIceCandidate(candidate)