from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import PassageOut, RechercheIn
from ..security import utilisateur_courant
from ..services import vector_store
from ..services.embeddings import vectoriser_question

router = APIRouter(prefix="/search", tags=["Recherche"])


@router.post("", response_model=list[PassageOut])
def rechercher_passages(
    requete: RechercheIn,
    user: User = Depends(utilisateur_courant),
    db: Session = Depends(get_db),
):
    vecteur = vectoriser_question(requete.question)
    return vector_store.rechercher(db, user.id, vecteur, requete.k)
