import os

from dotenv import load_dotenv

load_dotenv()  # lit le fichier .env, comme env() dans Laravel

# Base de données Supabase (PostgreSQL + pgvector)
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Embeddings : Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")
EMBEDDING_DIMENSION = 768  # taille des vecteurs : un bon compromis précision / stockage

# Génération des réponses : Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

SEUIL_SCORE = float(os.getenv("SEUIL_SCORE", "0.5"))

# Adresses du front autorisées à appeler l'API, séparées par des virgules
# Ex. : "http://localhost:5173,https://mon-front.vercel.app"
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
