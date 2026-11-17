from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import DATABASE_URL


def _adresse_sqlalchemy(url: str) -> str:
    # Supabase gives "postgresql://" URLs; force the psycopg (v3) driver.
    for prefixe in ("postgresql://", "postgres://"):
        if url.startswith(prefixe):
            return "postgresql+psycopg://" + url.removeprefix(prefixe)
    return url


engine = create_engine(
    _adresse_sqlalchemy(DATABASE_URL),
    pool_pre_ping=True,  # Supabase closes idle connections
    pool_size=5,
    max_overflow=5,
    # Disable prepared statements, required by Supabase's transaction pooler.
    connect_args={"prepare_threshold": None},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
