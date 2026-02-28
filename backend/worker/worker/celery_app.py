from __future__ import annotations

import os
import sys
from pathlib import Path

from celery import Celery
from dotenv import load_dotenv

# Allow worker to import `app.*` from backend/api without packaging.
API_DIR = (Path(__file__).resolve().parents[2] / "api").as_posix()
if API_DIR not in sys.path:
    sys.path.insert(0, API_DIR)

load_dotenv(".env")

from app.config import settings  # noqa: E402


celery_app = Celery(
    "doomlearn_worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

celery_app.autodiscover_tasks(["worker.tasks"])

