from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from .config import JWT_EXPIRATION_MINUTES, JWT_SECRET
from .database import get_db
from .models import User

ALGORITHME = "HS256"

hacheur = PasswordHash.recommended()
# Verified when the email is unknown, so login takes the same time either way.
HASH_FACTICE = hacheur.hash("mot-de-passe-factice")

schema_bearer = HTTPBearer(auto_error=False)


def hacher_mot_de_passe(mot_de_passe: str) -> str:
    return hacheur.hash(mot_de_passe)


def verifier_mot_de_passe(mot_de_passe: str, hash_: str | None) -> bool:
    if hash_ is None:
        hacheur.verify(mot_de_passe, HASH_FACTICE)
        return False
    return hacheur.verify(mot_de_passe, hash_)


def creer_jeton(user: User) -> str:
    expiration = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRATION_MINUTES)
    return jwt.encode({"sub": str(user.id), "exp": expiration}, JWT_SECRET, algorithm=ALGORITHME)


def utilisateur_courant(
    identifiants: HTTPAuthorizationCredentials | None = Depends(schema_bearer),
    db: Session = Depends(get_db),
) -> User:
    erreur = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Non authentifié ou session expirée.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if identifiants is None:
        raise erreur
    try:
        contenu = jwt.decode(identifiants.credentials, JWT_SECRET, algorithms=[ALGORITHME])
        user_id = int(contenu["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise erreur

    user = db.get(User, user_id)
    if user is None:
        raise erreur
    return user
