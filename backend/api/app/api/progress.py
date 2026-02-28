from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.db import get_db
from app.models import Course, User, UserProgress
from app.schemas import ProgressItemResponse, ProgressResponse

router = APIRouter()


@router.get("", response_model=ProgressResponse)
def get_progress(
    course_id: uuid.UUID = Query(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProgressResponse:
    course = db.query(Course).filter(Course.id == course_id, Course.user_id == user.id).one_or_none()
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")

    items = (
        db.query(UserProgress)
        .filter(UserProgress.user_id == user.id, UserProgress.course_id == course.id)
        .all()
    )
    return ProgressResponse(
        course_id=course.id,
        items=[
            ProgressItemResponse(
                topic_id=i.topic_id,
                mastery_score=i.mastery_score,
                last_seen_at=i.last_seen_at,
                next_review_at=i.next_review_at,
            )
            for i in items
        ],
    )

