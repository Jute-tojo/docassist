import json
import uuid

from fastapi import HTTPException
from google.genai import errors
from sqlalchemy.orm import Session

from ..config import SEUIL_SCORE
from ..models import Conversation, Message, User, now
from . import vector_store
from .embeddings import vectoriser_question
from .generation import REPONSE_INCONNUE, ServiceIASurcharge, generer_reponse

SURCHARGE = HTTPException(
    status_code=503,
    detail="Le service IA est momentanément surchargé. Réessayez dans quelques instants.",
    headers={"Retry-After": "30"},
)


def trouver_conversation(
    db: Session, user: User, conversation_id: uuid.UUID, source: str | None = None
) -> Conversation:
    conversation = db.get(Conversation, conversation_id)
    # Same 404 whether it does not exist or belongs to someone else: no information leak.
    if (
        conversation is None
        or conversation.user_id != user.id
        or (source is not None and conversation.source != source)
    ):
        raise HTTPException(status_code=404, detail="Conversation introuvable.")
    return conversation


def repondre(
    db: Session,
    user: User,
    question: str,
    conversation_id: uuid.UUID | None,
    k: int,
    source: str,
) -> tuple[Conversation, Message, bool]:
    if conversation_id is not None:
        conversation = trouver_conversation(db, user, conversation_id, source)
    else:
        conversation = Conversation(user_id=user.id, source=source, title=question[:80])
        db.add(conversation)

    historique = [{"role": m.role, "content": m.content} for m in conversation.messages]

    # Add the previous question so follow-ups like "and for managers?" find the right passages.
    precedentes = [m["content"] for m in historique if m["role"] == "user"]
    requete = f"{precedentes[-1]}\n{question}" if precedentes else question

    try:
        vecteur = vectoriser_question(requete)
        passages = [
            p for p in vector_store.rechercher(db, user.id, vecteur, k)
            if p["score"] >= SEUIL_SCORE
        ]
        reponse = (
            generer_reponse(question, passages, historique, user.description)
            if passages else REPONSE_INCONNUE
        )
    except ServiceIASurcharge:
        raise SURCHARGE
    except errors.APIError as erreur:  # Gemini embedding errors
        if erreur.code in (429, 503):
            raise SURCHARGE
        raise HTTPException(status_code=502, detail=f"Erreur du service IA : {erreur}")
    except HTTPException:
        raise
    except Exception as erreur:
        raise HTTPException(status_code=502, detail=f"Erreur du service IA : {erreur}")

    trouve = REPONSE_INCONNUE not in reponse
    if not trouve:
        passages = []

    sources = [
        {
            "numero": numero,
            "filename": p["filename"],
            "page": p["page"],
            "extrait": p["content"][:300],
            "score": p["score"],
        }
        for numero, p in enumerate(passages, start=1)
    ]

    conversation.messages.append(Message(role="user", content=question))
    message = Message(
        role="assistant",
        content=reponse,
        sources=json.dumps(sources, ensure_ascii=False),
    )
    conversation.messages.append(message)
    conversation.updated_at = now()
    db.commit()
    db.refresh(message)

    return conversation, message, trouve
