import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import WIDGET_REQUETES_PAR_MINUTE
from ..database import get_db
from ..models import User
from ..schemas import ChatIn, ChatOut, ConversationDetailOut
from ..services.limiteur import Limiteur
from ..services.rag import repondre, trouver_conversation

router = APIRouter(prefix="/widget", tags=["Widget (public)"])

limite_par_visiteur = Limiteur(WIDGET_REQUETES_PAR_MINUTE)
# Caps the AI cost of one account even if many visitors (or a bot) use its widget.
limite_par_compte = Limiteur(WIDGET_REQUETES_PAR_MINUTE * 6)


def _ip_visiteur(request: Request) -> str:
    # Render's proxy appends the real client IP at the end of X-Forwarded-For.
    transfert = request.headers.get("x-forwarded-for")
    if transfert:
        return transfert.split(",")[-1].strip()
    return request.client.host if request.client else "inconnue"


def proprietaire_widget(widget_key: str, request: Request, db: Session = Depends(get_db)) -> User:
    user = db.scalar(select(User).where(User.widget_key == widget_key))
    if user is None:
        raise HTTPException(status_code=404, detail="Widget introuvable.")

    if user.widget_origins:
        origine = (request.headers.get("origin") or "").rstrip("/").lower()
        if origine not in user.widget_origins.split(","):
            raise HTTPException(status_code=403, detail="Ce site n'est pas autorisé à utiliser ce widget.")
    return user


@router.post("/{widget_key}/chat", response_model=ChatOut)
def discuter_widget(
    requete: ChatIn,
    request: Request,
    user: User = Depends(proprietaire_widget),
    db: Session = Depends(get_db),
):
    if not limite_par_visiteur.autoriser(f"{user.id}:{_ip_visiteur(request)}") \
            or not limite_par_compte.autoriser(str(user.id)):
        raise HTTPException(
            status_code=429,
            detail="Trop de messages. Patientez une minute avant de réessayer.",
            headers={"Retry-After": "60"},
        )

    conversation, message, trouve = repondre(
        db, user, requete.question, requete.conversation_id, requete.k, source="widget"
    )
    return ChatOut(conversation_id=conversation.id, found=trouve, message=message)


@router.get("/{widget_key}/conversations/{conversation_id}", response_model=ConversationDetailOut)
def voir_conversation_widget(
    conversation_id: uuid.UUID,
    user: User = Depends(proprietaire_widget),
    db: Session = Depends(get_db),
):
    return trouver_conversation(db, user, conversation_id, source="widget")
