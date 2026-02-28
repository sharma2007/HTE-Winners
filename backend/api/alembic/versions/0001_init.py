"""init schema

Revision ID: 0001_init
Revises: 
Create Date: 2026-02-28

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector


revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(length=320)),
        sa.Column("name", sa.String(length=200)),
        sa.Column("auth_provider", sa.String(length=50), nullable=False),
        sa.Column("provider_sub", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("auth_provider", "provider_sub", name="uq_user_provider"),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_provider_sub", "users", ["provider_sub"])

    op.create_table(
        "courses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("reel_length_sec", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("review_frequency", sa.String(length=50), nullable=False, server_default="daily"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_courses_user_id", "courses", ["user_id"])

    op.create_table(
        "topics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id"), nullable=False),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("topics.id")),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_leaf", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_topics_course_id", "topics", ["course_id"])
    op.create_index("ix_topics_parent_id", "topics", ["parent_id"])

    op.create_table(
        "uploads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id"), nullable=False),
        sa.Column("type", sa.Enum("pdf", "video", name="upload_type"), nullable=False),
        sa.Column("object_key", sa.String(length=500), nullable=False),
        sa.Column("original_filename", sa.String(length=300)),
        sa.Column("status", sa.Enum("uploaded", "processing", "ready", "failed", name="upload_status"), nullable=False),
        sa.Column("metadata_json", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_uploads_course_id", "uploads", ["course_id"])

    op.create_table(
        "chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("upload_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("uploads.id"), nullable=False),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("topics.id")),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(384)),
        sa.Column("start_sec", sa.Float()),
        sa.Column("end_sec", sa.Float()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_chunks_upload_id", "chunks", ["upload_id"])
    op.create_index("ix_chunks_topic_id", "chunks", ["topic_id"])

    op.create_table(
        "reels",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id"), nullable=False),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("topics.id"), nullable=False),
        sa.Column("video_object_key", sa.String(length=500), nullable=False),
        sa.Column("captions_vtt", sa.Text()),
        sa.Column("duration_sec", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("source", sa.Enum("clip", "generated", name="reel_source"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_reels_course_id", "reels", ["course_id"])
    op.create_index("ix_reels_topic_id", "reels", ["topic_id"])

    op.create_table(
        "quizzes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id"), nullable=False),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("topics.id"), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("choices_json", sa.JSON()),
        sa.Column("answer_json", sa.JSON(), nullable=False),
        sa.Column("explanation", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_quizzes_course_id", "quizzes", ["course_id"])
    op.create_index("ix_quizzes_topic_id", "quizzes", ["topic_id"])

    op.create_table(
        "user_progress",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id"), nullable=False),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("topics.id"), nullable=False),
        sa.Column("mastery_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("last_seen_at", sa.DateTime(timezone=True)),
        sa.Column("next_review_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("user_id", "course_id", "topic_id", name="uq_user_course_topic"),
    )
    op.create_index("ix_user_progress_user_id", "user_progress", ["user_id"])
    op.create_index("ix_user_progress_course_id", "user_progress", ["course_id"])
    op.create_index("ix_user_progress_topic_id", "user_progress", ["topic_id"])

    op.create_table(
        "feed_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id"), nullable=False),
        sa.Column("reel_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reels.id")),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("topics.id")),
        sa.Column("event_type", sa.Enum(
            "watch",
            "skip",
            "replay",
            "like",
            "save",
            "share",
            "quiz_result",
            name="feed_event_type",
        ), nullable=False),
        sa.Column("watch_time_sec", sa.Float()),
        sa.Column("payload_json", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_feed_events_user_id", "feed_events", ["user_id"])
    op.create_index("ix_feed_events_course_id", "feed_events", ["course_id"])
    op.create_index("ix_feed_events_reel_id", "feed_events", ["reel_id"])
    op.create_index("ix_feed_events_topic_id", "feed_events", ["topic_id"])


def downgrade() -> None:
    op.drop_table("feed_events")
    op.drop_table("user_progress")
    op.drop_table("quizzes")
    op.drop_table("reels")
    op.drop_table("chunks")
    op.drop_table("uploads")
    op.drop_table("topics")
    op.drop_table("courses")
    op.drop_table("users")

    op.execute("DROP EXTENSION IF EXISTS vector")

