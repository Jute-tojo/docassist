import json

from fastapi import APIRouter, Depends, HTTPException, Query
from google.genai import errors
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import SEUIL_SCORE
from ..database import get_db
from ..models import Question
from ..schemas import QuestionIn, ReponseOut
from ..services import vector_store
from ..services.embeddings import vectoriser_question
from ..services.generation import REPONSE_INCONNUE, ServiceIASurcharge, generer_reponse

router = APIRouter(tags=["Assistant"])


def _vers_reponse(question: Question) -> ReponseOut:
    sources = json.loads(question.sources)
    return ReponseOut(
        id=question.id,
        question=question.question,
        answer=question.answer,
        found=len(sources) > 0,
        sources=sources,
        created_at=question.created_at,
    )


@router.post("/ask", response_model=ReponseOut)
def poser_question(requete: QuestionIn, db: Session = Depends(get_db)):
    try:
        vecteur = vectoriser_question(requete.question)
        passages = [
            p for p in vector_store.rechercher(db, vecteur, requete.k)
            if p["score"] >= SEUIL_SCORE
        ]
        reponse = generer_reponse(requete.question, passages) if passages else REPONSE_INCONNUE
    except ServiceIASurcharge:
        raise HTTPException(
            status_code=503,
            detail="Le service IA est momentanément surchargé. Réessayez dans quelques instants.",
            headers={"Retry-After": "30"},
        )
    except errors.APIError as erreur:  # Gemini embedding errors
        if erreur.code in (429, 503):
            raise HTTPException(
                status_code=503,
                detail="Le service IA est momentanément surchargé. Réessayez dans quelques instants.",
                headers={"Retry-After": "30"},
            )
        raise HTTPException(status_code=502, detail=f"Erreur du service IA : {erreur}")
    except Exception as erreur:
        raise HTTPException(status_code=502, detail=f"Erreur du service IA : {erreur}")

    # Drop sources when the model says the answer is not in the documents.
    if "Je ne trouve pas cette information" in reponse:
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

    question = Question(
        question=requete.question,
        answer=reponse,
        sources=json.dumps(sources, ensure_ascii=False),
    )
    db.add(question)
    db.commit()
    db.refresh(question)

    return _vers_reponse(question)


@router.get("/history", response_model=list[ReponseOut])
def historique(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    questions = db.scalars(
        select(Question).order_by(Question.created_at.desc()).limit(limit)
    ).all()
    return [_vers_reponse(q) for q in questions]