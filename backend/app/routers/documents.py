from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pypdf.errors import PdfReadError
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Chunk, Document
from ..schemas import ChunkOut, DocumentEnvoyeOut, DocumentOut
from ..services.chunking import decouper
from ..services.pdf import extraire_pages
from ..services.embeddings import vectoriser_morceaux

router = APIRouter(prefix="/documents", tags=["Documents"])

TAILLE_MAX = 10 * 1024 * 1024


@router.post("", response_model=DocumentEnvoyeOut, status_code=201)
def envoyer_document(
    fichier: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not fichier.filename or not fichier.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Seuls les fichiers PDF sont acceptés.")

    contenu = fichier.file.read()
    if len(contenu) > TAILLE_MAX:
        raise HTTPException(status_code=413, detail="Le fichier dépasse 10 Mo.")

    try:
        pages = extraire_pages(contenu)
    except PdfReadError:
        raise HTTPException(status_code=400, detail="Le PDF est illisible ou corrompu.")

    document = Document(filename=fichier.filename, nb_pages=len(pages))
    for numero_page, texte in enumerate(pages, start=1):
        for morceau in decouper(texte):
            document.chunks.append(
                Chunk(position=len(document.chunks), page=numero_page, content=morceau)
            )

    if not document.chunks:
        raise HTTPException(
            status_code=422,
            detail="Aucun texte trouvé dans ce PDF. S'agit-il d'un document scanné ?",
        )

    # Embed before saving so a failure leaves nothing half-indexed in the database.
    try:
        vecteurs = vectoriser_morceaux([chunk.content for chunk in document.chunks])
    except Exception as erreur:
        raise HTTPException(status_code=502, detail=f"Échec de l'indexation : {erreur}")

    for chunk, vecteur in zip(document.chunks, vecteurs):
        chunk.embedding = vecteur

    db.add(document)
    db.commit()
    db.refresh(document)

    return DocumentEnvoyeOut(
        id=document.id,
        filename=document.filename,
        nb_pages=document.nb_pages,
        created_at=document.created_at,
        nb_chunks=len(document.chunks),
    )


@router.get("", response_model=list[DocumentOut])
def lister_documents(db: Session = Depends(get_db)):
    return db.scalars(select(Document).order_by(Document.created_at.desc())).all()


@router.get("/{document_id}/chunks", response_model=list[ChunkOut])
def lister_morceaux(document_id: int, db: Session = Depends(get_db)):
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document introuvable.")
    return document.chunks


@router.delete("/{document_id}", status_code=204)
def supprimer_document(document_id: int, db: Session = Depends(get_db)):
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document introuvable.")
    db.delete(document)
    db.commit()