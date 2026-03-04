# ──────────────────────────────────────────────────────────────
# VeriTruth AI — WebSocket Router (Real-time Updates)
# ──────────────────────────────────────────────────────────────
from __future__ import annotations

import asyncio
import json
import logging
from typing import Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)
router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    """Manages WebSocket connections for real-time analysis updates."""

    def __init__(self):
        self._connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, analysis_id: str) -> None:
        await websocket.accept()
        if analysis_id not in self._connections:
            self._connections[analysis_id] = set()
        self._connections[analysis_id].add(websocket)
        logger.info("WS connected for analysis %s", analysis_id)

    def disconnect(self, websocket: WebSocket, analysis_id: str) -> None:
        if analysis_id in self._connections:
            self._connections[analysis_id].discard(websocket)
            if not self._connections[analysis_id]:
                del self._connections[analysis_id]

    async def send_update(self, analysis_id: str, data: dict) -> None:
        if analysis_id in self._connections:
            message = json.dumps(data)
            dead = set()
            for ws in self._connections[analysis_id]:
                try:
                    await ws.send_text(message)
                except Exception:
                    dead.add(ws)
            for ws in dead:
                self._connections[analysis_id].discard(ws)


manager = ConnectionManager()


async def _redis_progress_listener(websocket: WebSocket, analysis_id: str) -> None:
    """Subscribe to Redis pub/sub and forward progress messages to the WebSocket client."""
    try:
        import redis.asyncio as aioredis
        from app.core.config import get_settings
        settings = get_settings()
        r = aioredis.from_url(settings.REDIS_URL)
        pubsub = r.pubsub()
        channel = f"analysis:{analysis_id}:progress"
        await pubsub.subscribe(channel)
        logger.info("[WS] Subscribed to Redis channel: %s", channel)
        try:
            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                try:
                    payload = json.loads(message["data"])
                    await websocket.send_text(json.dumps(payload))
                    if payload.get("stage") == "done":
                        break
                except Exception as parse_err:
                    logger.warning("[WS] Could not parse Redis message: %s", parse_err)
        finally:
            await pubsub.unsubscribe(channel)
            await r.aclose()
    except Exception as e:
        logger.warning("[WS] Redis listener failed for %s: %s — falling back to polling", analysis_id, e)
        # Polling fallback: check DB status every 2 s and simulate progress ticks
        from sqlalchemy import select
        from app.core.database import async_session_factory
        from app.models.analysis import Analysis

        fake_pct = 0
        while True:
            await asyncio.sleep(2)
            fake_pct = min(fake_pct + 5, 90)
            try:
                async with async_session_factory() as session:
                    result = await session.execute(
                        select(Analysis).where(Analysis.id == analysis_id)
                    )
                    row = result.scalar_one_or_none()
                if row is None:
                    break
                if row.status in ("COMPLETED", "FAILED"):
                    # Send final done event so frontend transitions to results
                    await websocket.send_text(json.dumps({
                        "analysis_id": analysis_id,
                        "stage": "done",
                        "progress": 100,
                        "detail": "Analysis complete" if row.status == "COMPLETED" else "Analysis failed",
                    }))
                    break
                # Send a heartbeat tick so the progress bar moves
                await websocket.send_text(json.dumps({
                    "analysis_id": analysis_id,
                    "stage": "processing",
                    "progress": fake_pct,
                    "detail": "Processing…",
                }))
            except Exception:
                break


@router.websocket("/ws/analysis/{analysis_id}")
async def analysis_websocket(websocket: WebSocket, analysis_id: str):
    """WebSocket endpoint for real-time analysis progress updates.

    Subscribes to the Redis pub/sub channel published by the Celery worker
    and streams every progress event straight to the browser.  Falls back to
    DB-polling when Redis is unavailable.
    """
    await manager.connect(websocket, analysis_id)

    # Start the Redis listener as a background task
    listener_task = asyncio.create_task(
        _redis_progress_listener(websocket, analysis_id)
    )

    try:
        while True:
            # Keep connection alive and handle client ping/pong
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except asyncio.TimeoutError:
                # Send server-side ping to detect dead connections
                try:
                    await websocket.send_text(json.dumps({"type": "ping"}))
                except Exception:
                    break
            # Exit the loop once the listener task finishes (analysis done/failed)
            if listener_task.done():
                break
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error("WS error for %s: %s", analysis_id, e)
    finally:
        listener_task.cancel()
        manager.disconnect(websocket, analysis_id)
