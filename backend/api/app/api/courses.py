from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.db import get_db
from app.models import Course, Topic, User
from app.schemas import (
    CanvasImportResponse,
    CourseCreateRequest,
    CourseResponse,
    TopicCreateRequest,
    TopicResponse,
)

router = APIRouter()


@router.post("", response_model=CourseResponse)
def create_course(
    payload: CourseCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CourseResponse:
    course = Course(user_id=user.id, title=payload.title)
    db.add(course)
    db.commit()
    db.refresh(course)
    return CourseResponse(
        id=course.id,
        title=course.title,
        reel_length_sec=course.reel_length_sec,
        review_frequency=course.review_frequency,
    )


@router.get("", response_model=list[CourseResponse])
def list_courses(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[CourseResponse]:
    courses = db.query(Course).filter(Course.user_id == user.id).order_by(Course.created_at.desc()).all()
    return [
        CourseResponse(
            id=c.id,
            title=c.title,
            reel_length_sec=c.reel_length_sec,
            review_frequency=c.review_frequency,
        )
        for c in courses
    ]


@router.get("/{course_id}/topics", response_model=list[TopicResponse])
def list_topics(
    course_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[TopicResponse]:
    course = db.query(Course).filter(Course.id == course_id, Course.user_id == user.id).one_or_none()
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")

    topics = db.query(Topic).filter(Topic.course_id == course.id).order_by(Topic.order_index.asc()).all()
    return [
        TopicResponse(
            id=t.id,
            course_id=t.course_id,
            parent_id=t.parent_id,
            title=t.title,
            order_index=t.order_index,
            is_leaf=t.is_leaf,
        )
        for t in topics
    ]


@router.post("/{course_id}/topics", response_model=TopicResponse)
def create_topic(
    course_id: uuid.UUID,
    payload: TopicCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TopicResponse:
    course = db.query(Course).filter(Course.id == course_id, Course.user_id == user.id).one_or_none()
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")

    if payload.parent_id is not None:
        parent = (
            db.query(Topic)
            .filter(Topic.id == payload.parent_id, Topic.course_id == course.id)
            .one_or_none()
        )
        if parent is None:
            raise HTTPException(status_code=400, detail="parent_id not found")
        parent.is_leaf = False

    topic = Topic(course_id=course.id, parent_id=payload.parent_id, title=payload.title, order_index=payload.order_index)
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return TopicResponse(
        id=topic.id,
        course_id=topic.course_id,
        parent_id=topic.parent_id,
        title=topic.title,
        order_index=topic.order_index,
        is_leaf=topic.is_leaf,
    )


@router.post("/{course_id}/import/canvas", response_model=CanvasImportResponse)
def import_canvas_stub(
    course_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CanvasImportResponse:
    course = db.query(Course).filter(Course.id == course_id, Course.user_id == user.id).one_or_none()
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")

    # Stub structure until Canvas keys are wired.
    module_title = "Module 1: Foundations"
    subtopics = ["Intro concepts", "Key definitions", "Worked examples"]

    module = Topic(course_id=course.id, parent_id=None, title=module_title, order_index=0, is_leaf=False)
    db.add(module)
    db.flush()

    created: list[Topic] = [module]
    for i, st in enumerate(subtopics):
        t = Topic(course_id=course.id, parent_id=module.id, title=st, order_index=i, is_leaf=True)
        db.add(t)
        created.append(t)

    db.commit()

    created_topics = [
        TopicResponse(
            id=t.id,
            course_id=t.course_id,
            parent_id=t.parent_id,
            title=t.title,
            order_index=t.order_index,
            is_leaf=t.is_leaf,
        )
        for t in created
    ]
    return CanvasImportResponse(created_topics=created_topics)

