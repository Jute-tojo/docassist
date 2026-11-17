from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    nb_pages: int
    created_at: datetime


class DocumentEnvoyeOut(DocumentOut):
    nb_chunks: int


class ChunkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    position: int
    page: int
    content: str

class RechercheIn(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    k: int = Field(default=5, ge=1, le=10)


class PassageOut(BaseModel):
    chunk_id: int
    document_id: int
    filename: str
    page: int
    content: str
    score: float

class QuestionIn(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    k: int = Field(default=4, ge=1, le=10)


class SourceOut(BaseModel):
    numero: int
    filename: str
    page: int
    extrait: str
    score: float


class ReponseOut(BaseModel):
    id: int
    question: str
    answer: str
    found: bool
    sources: list[SourceOut]
    created_at: datetime