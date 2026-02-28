from __future__ import annotations

from celery import Celery

from app.config import settings


celery_client = Celery(
    "doomlearn_client",
    broker=settings.redis_url,
    backend=settings.redis_url,
)


def enqueue_process_upload(upload_id: str) -> None:
    celery_client.send_task("worker.tasks.process_upload", args=[upload_id])

