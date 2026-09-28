"""
database.py
-----------
Configurazione del database SQLAlchemy per il progetto
"Gestione Dispositivi Medici".
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from models import Base


# ============================================================
# CONFIGURAZIONE
# ============================================================

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./dispositivi_medici.db",
)


# ============================================================
# ENGINE
# ============================================================

connect_args = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args = {
        "check_same_thread": False
    }


engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    future=True,
)


# ============================================================
# SESSION
# ============================================================

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_db():
    """
    Crea le tabelle mancanti.

    Non elimina le tabelle o i dati già presenti.
    """

    Base.metadata.create_all(
        bind=engine
    )


# ============================================================
# FASTAPI DATABASE DEPENDENCY
# ============================================================

def get_db():
    """
    Fornisce una sessione SQLAlchemy alle API FastAPI.
    """

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# ============================================================
# COMPATIBILITÀ
# ============================================================

def get_session():
    """
    Compatibilità con il vecchio codice del progetto.

    Restituisce una normale sessione SQLAlchemy.
    """

    return SessionLocal()


# ============================================================
# DATABASE INFORMATION
# ============================================================

def get_database_tables():
    """
    Restituisce l'elenco delle tabelle presenti nel database.
    """

    inspector = inspect(engine)

    return inspector.get_table_names()


def database_status():
    """
    Restituisce lo stato del database.
    """

    tables = get_database_tables()

    return {
        "database_url": DATABASE_URL,
        "tables": tables,
        "initialized": len(tables) > 0,
    }


# ============================================================
# TEST / ESECUZIONE DIRETTA
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print(" INIZIALIZZAZIONE DATABASE")
    print("=" * 60)

    init_db()

    tables = get_database_tables()

    print()
    print("Database inizializzato correttamente.")
    print()
    print("Tabelle presenti:")

    for table in tables:
        print(f"  - {table}")

    print()
    print("=" * 60)