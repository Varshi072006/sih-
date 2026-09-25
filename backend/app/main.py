from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pathlib import Path
import sys

from app.config import settings
from app.database.session import Base, SessionLocal, engine
from app.models import *  # noqa: F401,F403
from app.api.auth import router as auth_router
from app.api.problems import router as problems_router
from app.api.government import router as government_router
from app.api.university import router as university_router
from app.api.industry import router as industry_router
from app.api.admin import router as admin_router
from app.api.projects import router as projects_router
from app.api.comms import router as comms_router
from app.api.public import router as public_router
from app.api.files import router as files_router
from app.api.ai import router as ai_router
from app.api.assistant import router as assistant_router
from app.api.ws import socket_app, start_broadcast_loop

sys.path.append(str(Path(__file__).resolve().parents[1]))
from seed.seed_data import seed_all

app = FastAPI(
    title="Challenge to Impact API",
    description="Jharkhand societal problem-solving collaboration platform. AI is decision-support only. Government remains the problem owner.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled(_request: Request, exc: Exception):
    from fastapi import HTTPException

    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    return JSONResponse(status_code=500, content={"detail": "Server error"})


@app.on_event("startup")
def startup():
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_all(db)
    finally:
        db.close()
    start_broadcast_loop()


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "challenge-to-impact"}


app.include_router(auth_router)
app.include_router(problems_router)
app.include_router(government_router)
app.include_router(university_router)
app.include_router(industry_router)
app.include_router(admin_router)
app.include_router(projects_router)
app.include_router(comms_router)
app.include_router(public_router)
app.include_router(files_router)
app.include_router(ai_router)
app.include_router(assistant_router)

# Mount Socket.IO only when python-socketio is installed
if socket_app is not None:
    app.mount("/", socket_app)
