import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")
# Must match the vector column size in the database; changing it requires re-indexing all documents.
EMBEDDING_DIMENSION = 768

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

SEUIL_SCORE = float(os.getenv("SEUIL_SCORE", "0.5"))

# Comma-separated, e.g. "http://localhost:5173,https://my-front.vercel.app"
CORS_ORIGINS = [
    origine.strip().rstrip("/")
    for origine in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if origine.strip()
]

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL est manquante dans le fichier .env (adresse Supabase)")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY est manquante dans le fichier .env")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY est manquante dans le fichier .env")
