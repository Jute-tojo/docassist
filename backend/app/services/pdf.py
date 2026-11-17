from io import BytesIO

from pypdf import PdfReader


def extraire_pages(contenu: bytes) -> list[str]:
    lecteur = PdfReader(BytesIO(contenu))
    return [(page.extract_text() or "").strip() for page in lecteur.pages]