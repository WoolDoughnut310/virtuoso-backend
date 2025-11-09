from fastapi import FastAPI, APIRouter, WebSocket
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.sdp import candidate_from_sdp
from contextlib import asynccontextmanager
import asyncio, json

from app.dependencies.db import SessionDep
from app.dependencies.concerts import ConcertDep
from app.routers.concerts import get_concert_manager

pcs = set()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await asyncio.gather(*[pc.close() for pc in pcs], return_exceptions=True)
    pcs.clear()


router = APIRouter(prefix="/concerts", lifespan=lifespan)


@router.websocket("/ws/{concert_id}")
async def websocket_endpoint(ws: WebSocket, concert: ConcertDep, session: SessionDep):
    assert concert.id is not None
    await ws.accept()

    cm = get_concert_manager(concert.id, session)

    pc = RTCPeerConnection()
    pcs.add(pc)
    pc.addTrack(cm.create_track())
    print(f"adding viewer connection for concert {concert.id}")

    @pc.on("icecandidate")
    async def on_icecandidate(candidate):
        if candidate:
            await ws.send_json({"type": "ice", "candidate": candidate.to_json()})

    try:
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
    except Exception:
        pass
    finally:
        pcs.discard(pc)
        await pc.close()
