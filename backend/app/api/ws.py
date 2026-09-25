"""
WebSocket / Socket.IO endpoint for the Live Collaboration Graph.

python-socketio is an optional dependency.  If it is not installed the
graph event bus still works (events are queued) but no WebSocket clients
will be served.  Install with:

    pip install "python-socketio[asyncio_client]" websockets
"""
import asyncio
import uuid
from collections import deque
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Optional socketio import
# ---------------------------------------------------------------------------
try:
    import socketio as _socketio
    _HAS_SOCKETIO = True
except ImportError:  # pragma: no cover
    _socketio = None
    _HAS_SOCKETIO = False

# ---------------------------------------------------------------------------
# In-process event bus
# ---------------------------------------------------------------------------

_recent_events: deque = deque(maxlen=50)


def get_recent_events(limit: int = 25) -> list:
    return list(_recent_events)[:limit]


class GraphEventBus:
    """Tiny async pub/sub bus.  Backend routers call .emit(); the Socket.IO
    broadcast loop subscribes and forwards to connected clients."""

    def __init__(self):
        self._queue: asyncio.Queue | None = None

    def _get_queue(self) -> asyncio.Queue:
        if self._queue is None:
            self._queue = asyncio.Queue()
        return self._queue

    def emit(self, event_type: str, payload: dict):
        """Fire-and-forget from sync FastAPI route handlers."""
        event = {
            "eventId": str(uuid.uuid4()),
            "type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **payload,
        }
        _recent_events.appendleft(event)
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.call_soon_threadsafe(self._get_queue().put_nowait, event)
        except RuntimeError:
            pass

    async def get(self) -> dict:
        return await self._get_queue().get()


graph_event_bus = GraphEventBus()

# ---------------------------------------------------------------------------
# Socket.IO server — only created when the package is available
# ---------------------------------------------------------------------------

if _HAS_SOCKETIO:
    sio = _socketio.AsyncServer(
        async_mode="asgi",
        cors_allowed_origins="*",
        logger=False,
        engineio_logger=False,
    )

    _presence: dict[str, set] = {}

    @sio.event
    async def connect(sid, environ, auth):
        pass

    @sio.event
    async def disconnect(sid):
        for room, members in list(_presence.items()):
            before = len(members)
            _presence[room] = {m for m in members if m[0] != sid}
            if len(_presence[room]) != before:
                await sio.emit(
                    "presence_update",
                    {"room": room, "count": len(_presence[room]),
                     "members": [m[1] for m in _presence[room]]},
                    room=room,
                )

    @sio.event
    async def join_graph(sid, data):
        room = data.get("room", "global")
        role_label = data.get("roleLabel", "Viewer")
        await sio.enter_room(sid, room)
        _presence.setdefault(room, set()).add((sid, role_label))
        await sio.emit(
            "presence_update",
            {"room": room, "count": len(_presence[room]),
             "members": [m[1] for m in _presence[room]]},
            room=room,
        )

    @sio.event
    async def leave_graph(sid, data):
        room = data.get("room", "global")
        await sio.leave_room(sid, room)
        if room in _presence:
            _presence[room] = {m for m in _presence[room] if m[0] != sid}
            await sio.emit(
                "presence_update",
                {"room": room, "count": len(_presence[room]),
                 "members": [m[1] for m in _presence[room]]},
                room=room,
            )

    @sio.event
    async def node_presence(sid, data):
        node_id = data.get("nodeId")
        active = data.get("active", True)
        await sio.emit(
            "node_presence_update",
            {"nodeId": node_id, "active": active, "sid": sid},
            room="global",
        )

    socket_app = _socketio.ASGIApp(sio, socketio_path="/ws/graph")

else:
    sio = None
    socket_app = None


# ---------------------------------------------------------------------------
# Background broadcast loop
# ---------------------------------------------------------------------------

async def _broadcast_loop():
    while True:
        event = await graph_event_bus.get()
        if sio is None:
            continue
        await sio.emit("graph_event", event, room="global")
        problem_id = event.get("problemId")
        if problem_id:
            await sio.emit("graph_event", event, room=f"problem:{problem_id}")


def start_broadcast_loop():
    """Called from FastAPI startup."""
    asyncio.ensure_future(_broadcast_loop())
