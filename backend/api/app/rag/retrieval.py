from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Chunk


def retrieve_top_k_chunks_for_topic(
    db: Session,
    upload_id,
    query_embedding: list[float],
    k: int = 6,
) -> list[Chunk]:
    """
    Lightweight pgvector retrieval. Requires `vector` extension and embeddings stored in `chunks.embedding`.
    """
    return (
        db.query(Chunk)
        .filter(Chunk.upload_id == upload_id)
        .filter(Chunk.embedding.is_not(None))
        .order_by(Chunk.embedding.cosine_distance(query_embedding))
        .limit(k)
        .all()
    )

