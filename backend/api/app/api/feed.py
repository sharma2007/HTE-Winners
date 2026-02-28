from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.db import get_db
from app.models import Course, Quiz, Reel, Topic, User, UserProgress
from app.schemas import FeedResponse, QuizResponse, ReelResponse
from app.storage.s3 import presign_get_url

router = APIRouter()


@router.get("", response_model=FeedResponse)
def get_feed(
    course_id: uuid.UUID = Query(...),
    limit: int = Query(5, ge=1, le=20),
    topic_ids: str | None = Query(None, description="Comma-separated topic UUIDs"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> FeedResponse:
    course = db.query(Course).filter(Course.id == course_id, Course.user_id == user.id).one_or_none()
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")

    topic_filter: set[uuid.UUID] | None = None
    if topic_ids:
        topic_filter = {uuid.UUID(t.strip()) for t in topic_ids.split(",") if t.strip()}

    q = db.query(Reel).filter(Reel.course_id == course.id).order_by(Reel.created_at.desc())
    if topic_filter:
        q = q.filter(Reel.topic_id.in_(topic_filter))
    reels = q.limit(limit).all()

    reel_responses = [
        ReelResponse(
            id=r.id,
            topic_id=r.topic_id,
            video_url=presign_get_url(r.video_object_key),
            captions_vtt=r.captions_vtt,
            duration_sec=r.duration_sec,
        )
        for r in reels
    ]

    # Choose a quiz for a due/weak topic (simple heuristic)
    quiz_obj = None
    progress = (
        db.query(UserProgress)
        .filter(UserProgress.user_id == user.id, UserProgress.course_id == course.id)
        .order_by(UserProgress.mastery_score.asc())
        .first()
    )
    if progress is not None:
        quiz_obj = (
            db.query(Quiz)
            .filter(Quiz.course_id == course.id, Quiz.topic_id == progress.topic_id)
            .order_by(Quiz.created_at.desc())
            .first()
        )

    quiz_response = None
    if quiz_obj is not None:
        quiz_response = QuizResponse(
            id=quiz_obj.id,
            topic_id=quiz_obj.topic_id,
            question=quiz_obj.question,
            choices=quiz_obj.choices_json,
        )

    return FeedResponse(reels=reel_responses, quiz=quiz_response)

