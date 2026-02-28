from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AuthGoogleRequest(BaseModel):
    id_token: str


class CourseCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class CourseResponse(BaseModel):
    id: uuid.UUID
    title: str
    reel_length_sec: int
    review_frequency: str


class TopicCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    parent_id: uuid.UUID | None = None
    order_index: int = 0


class TopicResponse(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    parent_id: uuid.UUID | None
    title: str
    order_index: int
    is_leaf: bool


class CanvasImportResponse(BaseModel):
    created_topics: list[TopicResponse]


class UploadCreateResponse(BaseModel):
    upload_id: uuid.UUID
    status: str


class UploadProcessResponse(BaseModel):
    upload_id: uuid.UUID
    enqueued: bool


class ReelResponse(BaseModel):
    id: uuid.UUID
    topic_id: uuid.UUID
    video_url: str
    captions_vtt: str | None
    duration_sec: int


class QuizResponse(BaseModel):
    id: uuid.UUID
    topic_id: uuid.UUID
    question: str
    choices: list[str] | None


class FeedResponse(BaseModel):
    reels: list[ReelResponse]
    quiz: QuizResponse | None = None


class WatchEventRequest(BaseModel):
    course_id: uuid.UUID
    reel_id: uuid.UUID | None = None
    topic_id: uuid.UUID | None = None
    event_type: Literal["watch", "skip", "replay", "like", "save", "share"]
    watch_time_sec: float | None = None


class QuizResultRequest(BaseModel):
    course_id: uuid.UUID
    quiz_id: uuid.UUID
    topic_id: uuid.UUID
    correct: bool
    selected: Any | None = None


class ProgressItemResponse(BaseModel):
    topic_id: uuid.UUID
    mastery_score: float
    last_seen_at: datetime | None
    next_review_at: datetime | None


class ProgressResponse(BaseModel):
    course_id: uuid.UUID
    items: list[ProgressItemResponse]

