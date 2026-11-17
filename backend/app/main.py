from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from . import models
from .config import CORS_ORIGINS
from .database import Base, engine
from .routers import ask, documents, search

# Active pgvector (une seule fois), puis crée les tables manquantes
with engine.begin() as connexion:
    connexion.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
Base.metadata.create_all(bind=engine)

# Sécurité Supabase : bloque l'accès aux tables via l'API REST publique (clé "anon").
# Le backend se connecte en propriétaire des tables, il n'est donc pas concerné.
with engine.begin() as connexion:
    for table in Base.metadata.tables:
        connexion.execute(text(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY'))

app = FastAPI(
    title="DocAssist",
    description="Assistant IA qui répond aux questions à partir de vos documents (RAG)",
    version="0.1.0",
)

# Autorise le front (Vue.js) à appeler l'API depuis une autre adresse
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(search.router)
app.include_router(ask.router)

@app.get("/health")
def health():
    return {"status": "ok"}