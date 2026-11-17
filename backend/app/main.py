from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from . import models
from .config import CORS_ORIGINS
from .database import Base, engine
from .routers import auth, chat, documents, search, widget

with engine.begin() as connexion:
    connexion.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
Base.metadata.create_all(bind=engine)

# Block access through Supabase's public REST API (anon key); the backend owns the tables, so it is not affected.
with engine.begin() as connexion:
    for table in Base.metadata.tables:
        connexion.execute(text(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY'))


class CORSParChemin:
    """Dashboard routes only accept CORS_ORIGINS; /widget/ routes accept any site
    (each account restricts its own widget with widget_origins)."""

    def __init__(self, app, origines_dashboard: list[str]):
        self.dashboard = CORSMiddleware(
            app, allow_origins=origines_dashboard, allow_methods=["*"], allow_headers=["*"]
        )
        self.widget = CORSMiddleware(
            app, allow_origins=["*"], allow_methods=["GET", "POST"], allow_headers=["Content-Type"]
        )

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope["path"].startswith("/widget/"):
            await self.widget(scope, receive, send)
        else:
            await self.dashboard(scope, receive, send)


app = FastAPI(
    title="DocAssist",
    description="SaaS : chaque compte crée son assistant IA à partir de ses propres documents (RAG)",
    version="0.2.0",
)

app.add_middleware(CORSParChemin, origines_dashboard=CORS_ORIGINS)

app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(search.router)
app.include_router(chat.router)
app.include_router(widget.router)


@app.get("/health")
def health():
    return {"status": "ok"}
