from __future__ import annotations

import boto3

from app.config import settings


def _client():
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        region_name=settings.s3_region,
        aws_access_key_id=settings.s3_access_key_id,
        aws_secret_access_key=settings.s3_secret_access_key,
    )


def put_object(object_key: str, data: bytes, content_type: str) -> None:
    c = _client()
    c.put_object(Bucket=settings.s3_bucket, Key=object_key, Body=data, ContentType=content_type)


def presign_get_url(object_key: str, expires_seconds: int = 3600) -> str:
    c = _client()
    return c.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.s3_bucket, "Key": object_key},
        ExpiresIn=expires_seconds,
    )

