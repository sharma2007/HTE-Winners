from __future__ import annotations

import os
import subprocess
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

from celery.utils.log import get_task_logger
from pypdf import PdfReader
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from worker.celery_app import celery_app

# Imports from backend/api/app via sys.path injection (see celery_app.py)
from app.config import settings  # noqa: E402
from app.minimax_client import (  # noqa: E402
    minimax_llm_generate_concepts,
    minimax_tts_generate_voice,
    minimax_video_generate,
)
from app.models import (  # noqa: E402
    Chunk,
    Course,
    Quiz,
    Reel,
    ReelSource,
    Topic,
    Upload,
    UploadStatus,
    UploadType,
    UserProgress,
)
from app.rag.chunking import chunk_text  # noqa: E402
from app.rag.embeddings import embed_text  # noqa: E402
from app.rag.prompt_pack import build_prompt_pack  # noqa: E402
from app.rag.retrieval import retrieve_top_k_chunks_for_topic  # noqa: E402
from app.storage.s3 import put_object  # noqa: E402

logger = get_task_logger(__name__)

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def _download_upload_bytes(upload: Upload) -> bytes:
    import boto3

    c = boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        region_name=settings.s3_region,
        aws_access_key_id=settings.s3_access_key_id,
        aws_secret_access_key=settings.s3_secret_access_key,
    )
    obj = c.get_object(Bucket=settings.s3_bucket, Key=upload.object_key)
    return obj["Body"].read()


def _extract_pdf_text(pdf_bytes: bytes) -> str:
    fd, path = tempfile.mkstemp(prefix="doomlearn_pdf_", suffix=".pdf")
    os.close(fd)
    Path(path).write_bytes(pdf_bytes)
    reader = PdfReader(path)
    parts = []
    for p in reader.pages:
        t = p.extract_text() or ""
        parts.append(t)
    return "\n\n".join(parts)


def _make_vtt_from_script(script_lines: list[str]) -> str:
    # Very simple WebVTT: each line gets ~3 seconds.
    out = ["WEBVTT", ""]
    t0 = 0.0
    for line in script_lines:
        t1 = t0 + 3.0
        out.append(f"{_fmt_ts(t0)} --> {_fmt_ts(t1)}")
        out.append(line.strip())
        out.append("")
        t0 = t1
    return "\n".join(out).strip() + "\n"


def _fmt_ts(sec: float) -> str:
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def _concat_script(reel_script: dict) -> list[str]:
    lines: list[str] = []
    hook = (reel_script or {}).get("hook")
    if hook:
        lines.append(str(hook))
    for st in (reel_script or {}).get("steps") or []:
        lines.append(str(st))
    cta = (reel_script or {}).get("cta")
    if cta:
        lines.append(str(cta))
    return [l for l in lines if l.strip()]


@celery_app.task(name="worker.tasks.process_upload")
def process_upload(upload_id: str) -> dict:
    db = SessionLocal()
    try:
        upload = db.query(Upload).filter(Upload.id == uuid.UUID(upload_id)).one_or_none()
        if upload is None:
            return {"ok": False, "error": "upload not found"}

        course = db.query(Course).filter(Course.id == upload.course_id).one()
        leaf_topics = (
            db.query(Topic)
            .filter(Topic.course_id == course.id, Topic.is_leaf.is_(True))
            .order_by(Topic.order_index.asc())
            .all()
        )

        raw = _download_upload_bytes(upload)

        if upload.type == UploadType.pdf:
            text = _extract_pdf_text(raw)
        else:
            # MVP: video transcription can be added here.
            text = "Transcript placeholder (video ASR not implemented in MVP)."

        chunks = chunk_text(text)
        for ch in chunks:
            emb = embed_text(ch.text)
            db.add(Chunk(upload_id=upload.id, topic_id=None, text=ch.text, embedding=emb))
        db.commit()

        # For each topic: retrieve top-k chunks, build prompt pack, call MiniMax (mockable)
        for t in leaf_topics[: max(1, min(len(leaf_topics), 8))]:
            q_emb = embed_text(t.title)
            top_chunks = retrieve_top_k_chunks_for_topic(db, upload.id, q_emb, k=6)
            pack = build_prompt_pack(t.title, [c.text for c in top_chunks])
            llm_out = minimax_llm_generate_concepts(
                {"topic_title": pack.topic_title, "facts": pack.facts, "target_length_sec": course.reel_length_sec}
            )
            reel_script = llm_out.get("reel_script") or {}
            script_lines = _concat_script(reel_script)
            vtt = _make_vtt_from_script(script_lines)

            # Generate media (mock: ffmpeg color video)
            _ = minimax_tts_generate_voice("\n".join(script_lines), voice_style="default")
            video_path = minimax_video_generate(
                prompt=f"Vertical reel about {t.title}",
                assets={"duration_sec": int(course.reel_length_sec)},
            )

            object_key = f"reels/{course.id}/{t.id}/{uuid.uuid4()}.mp4"
            put_object(object_key=object_key, data=Path(video_path).read_bytes(), content_type="video/mp4")

            reel = Reel(
                course_id=course.id,
                topic_id=t.id,
                video_object_key=object_key,
                captions_vtt=vtt,
                duration_sec=int(course.reel_length_sec),
                source=ReelSource.generated,
            )
            db.add(reel)

            quiz_items = llm_out.get("quiz_items") or []
            if quiz_items:
                qi = quiz_items[0]
                quiz = Quiz(
                    course_id=course.id,
                    topic_id=t.id,
                    question=str(qi.get("question") or f"Quick check: {t.title}?"),
                    choices_json=qi.get("choices"),
                    answer_json={"answer_index": qi.get("answer_index", 0)},
                    explanation=qi.get("explanation"),
                )
                db.add(quiz)

            up = (
                db.query(UserProgress)
                .filter(UserProgress.course_id == course.id, UserProgress.topic_id == t.id)
                .filter(UserProgress.user_id == course.user_id)
                .one_or_none()
            )
            if up is None:
                db.add(
                    UserProgress(
                        user_id=course.user_id,
                        course_id=course.id,
                        topic_id=t.id,
                        mastery_score=0.0,
                        last_seen_at=None,
                        next_review_at=datetime.now(timezone.utc),
                    )
                )

        upload.status = UploadStatus.ready
        db.commit()
        return {"ok": True, "upload_id": upload_id}
    except Exception as e:
        logger.exception("process_upload failed")
        try:
            upload = db.query(Upload).filter(Upload.id == uuid.UUID(upload_id)).one_or_none()
            if upload is not None:
                upload.status = UploadStatus.failed
                db.commit()
        except Exception:
            pass
        return {"ok": False, "error": str(e)}
    finally:
        db.close()

