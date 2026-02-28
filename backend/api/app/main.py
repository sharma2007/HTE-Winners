from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api import auth, courses, feed, uploads, events, progress


def create_app() -> FastAPI:
    app = FastAPI(title="DoomLearn API")

    origins = settings.cors_origins_list()
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(courses.router, prefix="/courses", tags=["courses"])
    app.include_router(uploads.router, prefix="/uploads", tags=["uploads"])
    app.include_router(feed.router, prefix="/feed", tags=["feed"])
    app.include_router(events.router, prefix="/events", tags=["events"])
    app.include_router(progress.router, prefix="/progress", tags=["progress"])

    @app.get("/health")
    def health() -> dict:
        return {"ok": True}

    return app


app = create_app()

