from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.config import settings
from app.db import get_db
from app.models import Course, Upload, UploadStatus, UploadType, User
from app.schemas import UploadCreateResponse, UploadProcessResponse
from app.storage.s3 import put_object

router = APIRouter()


@router.post("", response_model=UploadCreateResponse)
def create_upload(
    course_id: uuid.UUID = Form(...),
    type: UploadType = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> UploadCreateResponse:
    course = db.query(Course).filter(Course.id == course_id, Course.user_id == user.id).one_or_none()
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")

    ext = (file.filename or "").split(".")[-1].lower() if file.filename else ""
    key = f"uploads/{course_id}/{uuid.uuid4()}.{ext or 'bin'}"
    data = file.file.read()
    put_object(object_key=key, data=data, content_type=file.content_type or "application/octet-stream")

    upload = Upload(
        course_id=course.id,
        type=type,
        object_key=key,
        original_filename=file.filename,
        status=UploadStatus.uploaded,
        metadata_json={"content_type": file.content_type},
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)
    return UploadCreateResponse(upload_id=upload.id, status=upload.status.value)


@router.post("/{upload_id}/process", response_model=UploadProcessResponse)
def process_upload(
    upload_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> UploadProcessResponse:
    upload = (
        db.query(Upload)
        .join(Course, Course.id == Upload.course_id)
        .filter(Upload.id == upload_id)
        .filter(Course.user_id == user.id)
        .one_or_none()
    )
    if upload is None:
        raise HTTPException(status_code=404, detail="Upload not found")

    upload.status = UploadStatus.processing
    db.commit()

    # Celery enqueue via Redis
    from app.worker_client import enqueue_process_upload

    enqueue_process_upload(str(upload.id))
    return UploadProcessResponse(upload_id=upload.id, enqueued=True)

