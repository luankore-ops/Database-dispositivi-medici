"""
schemas.py
---------
Schemi Pydantic per la validazione delle richieste
e delle risposte dell'API "Gestione Dispositivi Medici".
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from models import (
    EsitoVerifica,
    RuoloUtente,
    StatoDispositivo,
    TipoManutenzione,
)


# ============================================================
# REPARTO
# ============================================================

class RepartoBase(BaseModel):
    nome: str = Field(
        min_length=1,
        max_length=100,
    )

    piano: Optional[str] = Field(
        default=None,
        max_length=20,
    )


class RepartoCreate(RepartoBase):
    pass


class RepartoRead(RepartoBase):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int


# ============================================================
# FORNITORE
# ============================================================

class FornitoreBase(BaseModel):
    ragione_sociale: str = Field(
        min_length=1,
        max_length=150,
    )

    email_contatto: Optional[str] = Field(
        default=None,
        max_length=150,
    )

    telefono: Optional[str] = Field(
        default=None,
        max_length=30,
    )


class FornitoreCreate(FornitoreBase):
    pass


class FornitoreRead(FornitoreBase):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int


# ============================================================
# DISPOSITIVO
# ============================================================

class DispositivoBase(BaseModel):
    nome: str = Field(
        min_length=1,
        max_length=150,
    )

    categoria: str = Field(
        min_length=1,
        max_length=100,
    )

    numero_seriale: str = Field(
        min_length=1,
        max_length=100,
    )

    udi: Optional[str] = Field(
        default=None,
        max_length=100,
    )

    produttore: str = Field(
        min_length=1,
        max_length=150,
    )

    modello: Optional[str] = Field(
        default=None,
        max_length=100,
    )

    data_acquisto: Optional[date] = None

    costo: Optional[float] = None

    data_scadenza_garanzia: Optional[date] = None

    stato: StatoDispositivo = (
        StatoDispositivo.IN_USO
    )

    reparto_id: Optional[int] = None

    fornitore_id: Optional[int] = None


class DispositivoCreate(DispositivoBase):
    pass


class DispositivoUpdate(BaseModel):
    nome: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=150,
    )

    categoria: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    numero_seriale: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    udi: Optional[str] = Field(
        default=None,
        max_length=100,
    )

    produttore: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=150,
    )

    modello: Optional[str] = Field(
        default=None,
        max_length=100,
    )

    costo: Optional[float] = None

    stato: Optional[StatoDispositivo] = None

    reparto_id: Optional[int] = None

    fornitore_id: Optional[int] = None

    data_scadenza_garanzia: Optional[date] = None


class DispositivoRead(DispositivoBase):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int


# ============================================================
# MANUTENZIONE
# ============================================================

class ManutenzioneBase(BaseModel):
    data: date

    tipo: TipoManutenzione

    tecnico: Optional[str] = Field(
        default=None,
        max_length=100,
    )

    descrizione: Optional[str] = Field(
        default=None,
        max_length=2000,
    )

    prossima_scadenza: Optional[date] = None


class ManutenzioneCreate(ManutenzioneBase):
    pass


class ManutenzioneRead(ManutenzioneBase):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int

    dispositivo_id: int


# ============================================================
# CALIBRAZIONE
# ============================================================

class CalibrazioneBase(BaseModel):
    data: date

    esito: EsitoVerifica

    ente_certificatore: Optional[str] = Field(
        default=None,
        max_length=150,
    )

    prossima_scadenza: Optional[date] = None


class CalibrazioneCreate(CalibrazioneBase):
    pass


class CalibrazioneRead(CalibrazioneBase):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int

    dispositivo_id: int


# ============================================================
# SCADENZE
# ============================================================

class ScadenzaItem(BaseModel):
    dispositivo_id: int

    dispositivo_nome: str

    tipo_scadenza: str

    data_scadenza: date

    giorni_rimanenti: int


# ============================================================
# UTENTI
# ============================================================

class UtenteBase(BaseModel):
    username: str = Field(
        min_length=1,
        max_length=100,
    )

    ruolo: RuoloUtente = (
        RuoloUtente.LETTORE
    )

    attivo: bool = True


class UtenteCreate(UtenteBase):
    password: str = Field(
        min_length=12,
        max_length=255,
    )


class UtenteUpdate(BaseModel):
    username: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    ruolo: Optional[RuoloUtente] = None

    attivo: Optional[bool] = None


class UtentePasswordUpdate(BaseModel):
    password: str = Field(
        min_length=12,
        max_length=255,
    )


class UtenteStatoUpdate(BaseModel):
    attivo: bool


class UtenteRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int

    username: str

    ruolo: RuoloUtente

    attivo: bool

    creato_il: datetime