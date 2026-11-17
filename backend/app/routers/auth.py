from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, nouvelle_cle_widget
from ..schemas import ConnexionIn, InscriptionIn, JetonOut, ProfilIn, UserOut
from ..security import creer_jeton, hacher_mot_de_passe, utilisateur_courant, verifier_mot_de_passe

router = APIRouter(prefix="/auth", tags=["Compte"])


def _normaliser_origine(origine: str) -> str:
    return origine.strip().rstrip("/").lower()


@router.post("/register", response_model=JetonOut, status_code=201)
def inscription(donnees: InscriptionIn, db: Session = Depends(get_db)):
    email = donnees.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Un compte existe déjà avec cet email.")

    user = User(
        email=email,
        password_hash=hacher_mot_de_passe(donnees.password),
        description=donnees.description.strip(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return JetonOut(access_token=creer_jeton(user), user=user)


@router.post("/login", response_model=JetonOut)
def connexion(donnees: ConnexionIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == donnees.email.lower()))
    if not verifier_mot_de_passe(donnees.password, user.password_hash if user else None):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect.")
    return JetonOut(access_token=creer_jeton(user), user=user)


@router.get("/me", response_model=UserOut)
def mon_compte(user: User = Depends(utilisateur_courant)):
    return user


@router.patch("/me", response_model=UserOut)
def modifier_compte(
    donnees: ProfilIn,
    user: User = Depends(utilisateur_courant),
    db: Session = Depends(get_db),
):
    if donnees.description is not None:
        user.description = donnees.description.strip()
    if donnees.widget_origins is not None:
        origines = {_normaliser_origine(o) for o in donnees.widget_origins if o.strip()}
        for origine in origines:
            if not origine.startswith(("http://", "https://")):
                raise HTTPException(
                    status_code=422,
                    detail=f"Origine invalide : « {origine} ». Exemple : https://monsite.com",
                )
        user.widget_origins = ",".join(sorted(origines))
    db.commit()
    db.refresh(user)
    return user


@router.post("/me/widget-key", response_model=UserOut)
def regenerer_cle_widget(user: User = Depends(utilisateur_courant), db: Session = Depends(get_db)):
    user.widget_key = nouvelle_cle_widget()
    db.commit()
    db.refresh(user)
    return user


@router.delete("/me", status_code=204)
def supprimer_compte(user: User = Depends(utilisateur_courant), db: Session = Depends(get_db)):
    db.delete(user)
    db.commit()
