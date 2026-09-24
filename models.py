"""
models.py — Modelli SQLAlchemy per il progetto "Gestione Dispositivi Medici"

Schema:
    Reparto 1---N Dispositivo N---1 Fornitore
    Dispositivo 1---N Manutenzione
    Dispositivo 1---N Calibrazione
    AuditLog (tabella indipendente, traccia le modifiche)
"""

from datetime import date, datetime
from enum import Enum as PyEnum
from typing import Optional, List

from sqlalchemy import String, Float, Date, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# --- Enum di dominio -------------------------------------------------------

class StatoDispositivo(PyEnum):
    IN_USO = "in_uso"
    MANUTENZIONE = "manutenzione"
    GUASTO = "guasto"
    DISMESSO = "dismesso"


class TipoManutenzione(PyEnum):
    PREVENTIVA = "preventiva"
    CORRETTIVA = "correttiva"


class EsitoVerifica(PyEnum):
    CONFORME = "conforme"
    NON_CONFORME = "non_conforme"


# --- Entità anagrafiche ------------------------------------------------------

class Reparto(Base):
    __tablename__ = "reparti"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    piano: Mapped[Optional[str]] = mapped_column(String(20))

    dispositivi: Mapped[List["Dispositivo"]] = relationship(back_populates="reparto")

    def __repr__(self) -> str:
        return f"<Reparto {self.nome}>"


class Fornitore(Base):
    __tablename__ = "fornitori"

    id: Mapped[int] = mapped_column(primary_key=True)
    ragione_sociale: Mapped[str] = mapped_column(String(150), nullable=False)
    email_contatto: Mapped[Optional[str]] = mapped_column(String(150))
    telefono: Mapped[Optional[str]] = mapped_column(String(30))

    dispositivi: Mapped[List["Dispositivo"]] = relationship(back_populates="fornitore")

    def __repr__(self) -> str:
        return f"<Fornitore {self.ragione_sociale}>"


# --- Entità principale -------------------------------------------------------

class Dispositivo(Base):
    __tablename__ = "dispositivi"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    categoria: Mapped[str] = mapped_column(String(100), nullable=False)  # es. diagnostica, terapia, monitoraggio
    numero_seriale: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    udi: Mapped[Optional[str]] = mapped_column(String(100), unique=True)  # Unique Device Identification (MDR 2017/745)
    produttore: Mapped[str] = mapped_column(String(150), nullable=False)
    modello: Mapped[Optional[str]] = mapped_column(String(100))

    data_acquisto: Mapped[Optional[date]] = mapped_column(Date)
    costo: Mapped[Optional[float]] = mapped_column(Float)
    data_scadenza_garanzia: Mapped[Optional[date]] = mapped_column(Date)

    stato: Mapped[StatoDispositivo] = mapped_column(
        Enum(StatoDispositivo), default=StatoDispositivo.IN_USO, nullable=False
    )

    reparto_id: Mapped[Optional[int]] = mapped_column(ForeignKey("reparti.id"))
    fornitore_id: Mapped[Optional[int]] = mapped_column(ForeignKey("fornitori.id"))

    reparto: Mapped[Optional["Reparto"]] = relationship(back_populates="dispositivi")
    fornitore: Mapped[Optional["Fornitore"]] = relationship(back_populates="dispositivi")
    manutenzioni: Mapped[List["Manutenzione"]] = relationship(
        back_populates="dispositivo", cascade="all, delete-orphan"
    )
    calibrazioni: Mapped[List["Calibrazione"]] = relationship(
        back_populates="dispositivo", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Dispositivo {self.nome} (SN:{self.numero_seriale})>"


# --- Entità storiche ----------------------------------------------------

class Manutenzione(Base):
    __tablename__ = "manutenzioni"

    id: Mapped[int] = mapped_column(primary_key=True)
    dispositivo_id: Mapped[int] = mapped_column(ForeignKey("dispositivi.id"), nullable=False)

    data: Mapped[date] = mapped_column(Date, nullable=False)
    tipo: Mapped[TipoManutenzione] = mapped_column(Enum(TipoManutenzione), nullable=False)
    tecnico: Mapped[Optional[str]] = mapped_column(String(100))
    descrizione: Mapped[Optional[str]] = mapped_column(Text)
    prossima_scadenza: Mapped[Optional[date]] = mapped_column(Date)

    dispositivo: Mapped["Dispositivo"] = relationship(back_populates="manutenzioni")

    def __repr__(self) -> str:
        return f"<Manutenzione {self.tipo.value} - {self.data}>"


class Calibrazione(Base):
    __tablename__ = "calibrazioni"

    id: Mapped[int] = mapped_column(primary_key=True)
    dispositivo_id: Mapped[int] = mapped_column(ForeignKey("dispositivi.id"), nullable=False)

    data: Mapped[date] = mapped_column(Date, nullable=False)
    esito: Mapped[EsitoVerifica] = mapped_column(Enum(EsitoVerifica), nullable=False)
    ente_certificatore: Mapped[Optional[str]] = mapped_column(String(150))
    prossima_scadenza: Mapped[Optional[date]] = mapped_column(Date)

    dispositivo: Mapped["Dispositivo"] = relationship(back_populates="calibrazioni")

    def __repr__(self) -> str:
        return f"<Calibrazione {self.esito.value} - {self.data}>"


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    utente: Mapped[str] = mapped_column(String(100), nullable=False)
    azione: Mapped[str] = mapped_column(String(50), nullable=False)  # CREATE, UPDATE, DELETE
    tabella: Mapped[str] = mapped_column(String(50), nullable=False)
    dettagli: Mapped[Optional[str]] = mapped_column(Text)

    def __repr__(self) -> str:
        return f"<AuditLog {self.azione} su {self.tabella} @ {self.timestamp}>"
