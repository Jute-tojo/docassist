import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Conversation, User
from ..schemas import ChatIn, ChatOut, ConversationDetailOut, ConversationOut
from ..security import utilisateur_courant
from ..services.rag import repondre, trouver_conversation

router = APIRouter(tags=["Chat"])


@router.post("/chat", response_model=ChatOut)
def discuter(
    requete: ChatIn,
    user: User = Depends(utilisateur_courant),
    db: Session = Depends(get_db),
):
    conversation, message, trouve = repondre(
        db, user, requete.question, requete.conversation_id, requete.k, source="app"
    )
    return ChatOut(conversation_id=conversation.id, found=trouve, message=message)


@router.get("/conversations", response_model=list[ConversationOut])
def lister_conversations(
    source: str | None = Query(default=None, pattern="^(app|widget)$"),
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(utilisateur_courant),
    db: Session = Depends(get_db),
):
    requete = select(Conversation).where(Conversation.user_id == user.id)
    if source:
        requete = requete.where(Conversation.source == source)
    return db.scalars(requete.order_by(Conversation.updated_at.desc()).limit(limit)).all()


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailOut)
def voir_conversation(
    conversation_id: uuid.UUID,
    user: User = Depends(utilisateur_courant),
    db: Session = Depends(get_db),
):
    return trouver_conversation(db, user, conversation_id)


@router.delete("/conversations/{conversation_id}", status_code=204)
def supprimer_conversation(
    conversation_id: uuid.UUID,
    user: User = Depends(utilisateur_courant),
    db: Session = Depends(get_db),
):
    db.delete(trouver_conversation(db, user, conversation_id))
    db.commit()
