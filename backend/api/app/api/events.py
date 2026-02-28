from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.db import get_db
from app.models import Course, FeedEvent, FeedEventType, Quiz, User, UserProgress
from app.schemas import QuizResultRequest, WatchEventRequest

router = APIRouter()


def _schedule_next_review(mastery: float) -> datetime:
    # Very lightweight spaced repetition schedule.
    if mastery < 0.3:
        delta = timedelta(days=1)
    elif mastery < 0.7:
        delta = timedelta(days=3)
    else:
        delta = timedelta(days=7)
    return datetime.now(timezone.utc) + delta


@router.post("/watch")
def watch_event(
    payload: WatchEventRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    course = db.query(Course).filter(Course.id == payload.course_id, Course.user_id == user.id).one_or_none()
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")

    event = FeedEvent(
        user_id=user.id,
        course_id=course.id,
        reel_id=payload.reel_id,
        topic_id=payload.topic_id,
        event_type=FeedEventType(payload.event_type),
        watch_time_sec=payload.watch_time_sec,
        payload_json=None,
    )
    db.add(event)

    # Small mastery nudge for watch time on a topic.
    if payload.topic_id and payload.event_type == "watch" and payload.watch_time_sec is not None:
        up = (
            db.query(UserProgress)
            .filter(
                UserProgress.user_id == user.id,
                UserProgress.course_id == course.id,
                UserProgress.topic_id == payload.topic_id,
            )
            .one_or_none()
        )
        if up is None:
            up = UserProgress(user_id=user.id, course_id=course.id, topic_id=payload.topic_id, mastery_score=0.0)
            db.add(up)
        up.mastery_score = min(1.0, up.mastery_score + min(0.05, payload.watch_time_sec / 300.0))
        up.last_seen_at = datetime.now(timezone.utc)
        up.next_review_at = _schedule_next_review(up.mastery_score)

    db.commit()
    return {"ok": True}


@router.post("/quiz_result")
def quiz_result(
    payload: QuizResultRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    course = db.query(Course).filter(Course.id == payload.course_id, Course.user_id == user.id).one_or_none()
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")

    quiz = db.query(Quiz).filter(Quiz.id == payload.quiz_id, Quiz.course_id == course.id).one_or_none()
    if quiz is None:
        raise HTTPException(status_code=404, detail="Quiz not found")

    event = FeedEvent(
        user_id=user.id,
        course_id=course.id,
        reel_id=None,
        topic_id=payload.topic_id,
        event_type=FeedEventType.quiz_result,
        watch_time_sec=None,
        payload_json={"correct": payload.correct, "selected": payload.selected},
    )
    db.add(event)

    up = (
        db.query(UserProgress)
        .filter(UserProgress.user_id == user.id, UserProgress.course_id == course.id, UserProgress.topic_id == payload.topic_id)
        .one_or_none()
    )
    if up is None:
        up = UserProgress(user_id=user.id, course_id=course.id, topic_id=payload.topic_id, mastery_score=0.0)
        db.add(up)

    up.mastery_score = min(1.0, up.mastery_score + (0.2 if payload.correct else -0.1))
    up.mastery_score = max(0.0, up.mastery_score)
    up.last_seen_at = datetime.now(timezone.utc)
    up.next_review_at = _schedule_next_review(up.mastery_score)

    db.commit()
    return {"ok": True, "mastery_score": up.mastery_score, "next_review_at": up.next_review_at}

