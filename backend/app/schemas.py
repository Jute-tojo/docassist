import json
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class InscriptionIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    description: str = Field(default="", max_length=2000)


class ConnexionIn(BaseModel):
    email: EmailStr
    password: str = Field(max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    description: str
    widget_key: str
    widget_origins: list[str]
    created_at: datetime

    @field_validator("widget_origins", mode="before")
    @classmethod
    def _decouper_origines(cls, valeur):
        if isinstance(valeur, str):
            return [o for o in valeur.split(",") if o]
        return valeur


class JetonOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ProfilIn(BaseModel):
    description: str | None = Field(default=None, max_length=2000)
    widget_origins: list[str] | None = Field(default=None, max_length=20)


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


class SourceOut(BaseModel):
    numero: int
    filename: str
    page: int
    extrait: str
    score: float


class ChatIn(BaseModel):
    question: str = Field(min_length=2, max_length=500)
    conversation_id: uuid.UUID | None = None
    k: int = Field(default=4, ge=1, le=10)


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    sources: list[SourceOut]
    created_at: datetime

    @field_validator("sources", mode="before")
    @classmethod
    def _lire_json(cls, valeur):
        return json.loads(valeur) if isinstance(valeur, str) else valeur


class ChatOut(BaseModel):
    conversation_id: uuid.UUID
    found: bool
    message: MessageOut


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    source: str
    created_at: datetime
    updated_at: datetime


class ConversationDetailOut(ConversationOut):
    messages: list[MessageOut]
