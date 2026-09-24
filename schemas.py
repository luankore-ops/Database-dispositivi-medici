"""
schemas.py — Schemi Pydantic per la validazione delle richieste/risposte dell'API
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict

from models import StatoDispositivo, TipoManutenzione, EsitoVerifica


# --- Reparto ---

class RepartoBase(BaseModel):
    nome: str
    piano: Optional[str] = None


class RepartoCreate(RepartoBase):
    pass


class RepartoRead(RepartoBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# --- Fornitore ---

class FornitoreBase(BaseModel):
    ragione_sociale: str
    email_contatto: Optional[str] = None
    telefono: Optional[str] = None


class FornitoreCreate(FornitoreBase):
    pass


class FornitoreRead(FornitoreBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# --- Dispositivo ---

class DispositivoBase(BaseModel):
    nome: str
    categoria: str
    numero_seriale: str
    udi: Optional[str] = None
    produttore: str
    modello: Optional[str] = None
    data_acquisto: Optional[date] = None
    costo: Optional[float] = None
    data_scadenza_garanzia: Optional[date] = None
    stato: StatoDispositivo = StatoDispositivo.IN_USO
    reparto_id: Optional[int] = None
    fornitore_id: Optional[int] = None


class DispositivoCreate(DispositivoBase):
    pass


class DispositivoUpdate(BaseModel):
    nome: Optional[str] = None
    categoria: Optional[str] = None
    numero_seriale: Optional[str] = None
    udi: Optional[str] = None
    produttore: Optional[str] = None
    modello: Optional[str] = None
    costo: Optional[float] = None
    stato: Optional[StatoDispositivo] = None
    reparto_id: Optional[int] = None
    fornitore_id: Optional[int] = None
    data_scadenza_garanzia: Optional[date] = None


class DispositivoRead(DispositivoBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# --- Manutenzione ---

class ManutenzioneBase(BaseModel):
    data: date
    tipo: TipoManutenzione
    tecnico: Optional[str] = None
    descrizione: Optional[str] = None
    prossima_scadenza: Optional[date] = None


class ManutenzioneCreate(ManutenzioneBase):
    pass


class ManutenzioneRead(ManutenzioneBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    dispositivo_id: int


# --- Calibrazione ---

class CalibrazioneBase(BaseModel):
    data: date
    esito: EsitoVerifica
    ente_certificatore: Optional[str] = None
    prossima_scadenza: Optional[date] = None


class CalibrazioneCreate(CalibrazioneBase):
    pass


class CalibrazioneRead(CalibrazioneBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    dispositivo_id: int


# --- Scadenze ---

class ScadenzaItem(BaseModel):
    dispositivo_id: int
    dispositivo_nome: str
    tipo_scadenza: str  # "manutenzione" o "calibrazione"
    data_scadenza: date
    giorni_rimanenti: int