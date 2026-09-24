"""
database.py — Configurazione engine e sessione SQLAlchemy
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from models import Base

# Per sviluppo locale: SQLite (file singolo, zero configurazione)
DATABASE_URL = "sqlite:///dispositivi_medici.db"

# Per produzione, basta cambiare la URL (nessuna modifica al resto del codice):
# DATABASE_URL = "postgresql+psycopg2://user:password@localhost:5432/dispositivi_medici"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    """Crea tutte le tabelle nel database, se non esistono già."""
    Base.metadata.create_all(bind=engine)


def get_session() -> Session:
    """Restituisce una nuova sessione. Ricordarsi di chiuderla (o usarla come context manager)."""
    return SessionLocal()
