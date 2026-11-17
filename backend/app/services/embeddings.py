from google import genai
from google.genai import types

from ..config import EMBEDDING_DIMENSION, EMBEDDING_MODEL, GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)

DIMENSION = EMBEDDING_DIMENSION
TAILLE_LOT = 50   # nombre de textes envoyés à Gemini par requête


def _vectoriser(textes: list[str], task_type: str) -> list[list[float]]:
    vecteurs = []
    for debut in range(0, len(textes), TAILLE_LOT):
        lot = textes[debut:debut + TAILLE_LOT]
        resultat = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=lot,
            config=types.EmbedContentConfig(
                task_type=task_type,
                output_dimensionality=DIMENSION,
            ),
        )
        vecteurs.extend(embedding.values for embedding in resultat.embeddings)
    return vecteurs


def vectoriser_morceaux(textes: list[str]) -> list[list[float]]:
    return _vectoriser(textes, "RETRIEVAL_DOCUMENT")


def vectoriser_question(question: str) -> list[float]:
    return _vectoriser([question], "RETRIEVAL_QUERY")[0]