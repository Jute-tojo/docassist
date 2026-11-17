from sqlalchemy import select, text
from sqlalchemy.orm import Session

from ..models import Chunk, Document


def rechercher(db: Session, user_id: int, vecteur: list[float], k: int = 5) -> list[dict]:
    # Keep scanning the HNSW index until k rows match the account filter (pgvector >= 0.8).
    db.execute(text("SET LOCAL hnsw.iterative_scan = relaxed_order"))

    distance = Chunk.embedding.cosine_distance(vecteur).label("distance")
    lignes = db.execute(
        select(Chunk, Document.filename, distance)
        .join(Document, Chunk.document_id == Document.id)
        .where(Chunk.user_id == user_id)
        .order_by(distance)
        .limit(k)
    ).all()

    return [
        {
            "chunk_id": chunk.id,
            "document_id": chunk.document_id,
            "filename": filename,
            "page": chunk.page,
            "content": chunk.content,
            "score": round(1 - dist, 3),  # Cosine similarity: 1 = same meaning, 0 = unrelated
        }
        for chunk, filename, dist in lignes
    ]
