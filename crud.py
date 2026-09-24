"""
crud.py — Funzioni di accesso al database (Create, Read, Update, Delete)
"""

from datetime import date, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import select

import models
import schemas


# --- Reparto ---

def crea_reparto(db: Session, reparto: schemas.RepartoCreate) -> models.Reparto:
    db_reparto = models.Reparto(**reparto.model_dump())
    db.add(db_reparto)
    db.commit()
    db.refresh(db_reparto)
    return db_reparto


def lista_reparti(db: Session) -> List[models.Reparto]:
    return list(db.scalars(select(models.Reparto)).all())


# --- Fornitore ---

def crea_fornitore(db: Session, fornitore: schemas.FornitoreCreate) -> models.Fornitore:
    db_fornitore = models.Fornitore(**fornitore.model_dump())
    db.add(db_fornitore)
    db.commit()
    db.refresh(db_fornitore)
    return db_fornitore


def lista_fornitori(db: Session) -> List[models.Fornitore]:
    return list(db.scalars(select(models.Fornitore)).all())


# --- Dispositivo ---

def crea_dispositivo(db: Session, dispositivo: schemas.DispositivoCreate) -> models.Dispositivo:
    db_dispositivo = models.Dispositivo(**dispositivo.model_dump())
    db.add(db_dispositivo)
    db.commit()
    db.refresh(db_dispositivo)
    return db_dispositivo


def lista_dispositivi(
    db: Session, categoria: Optional[str] = None, stato: Optional[models.StatoDispositivo] = None
) -> List[models.Dispositivo]:
    stmt = select(models.Dispositivo)
    if categoria:
        stmt = stmt.where(models.Dispositivo.categoria == categoria)
    if stato:
        stmt = stmt.where(models.Dispositivo.stato == stato)
    return list(db.scalars(stmt).all())


def get_dispositivo(db: Session, dispositivo_id: int) -> Optional[models.Dispositivo]:
    return db.get(models.Dispositivo, dispositivo_id)


def aggiorna_dispositivo(
    db: Session, dispositivo_id: int, dati: schemas.DispositivoUpdate
) -> Optional[models.Dispositivo]:
    db_dispositivo = get_dispositivo(db, dispositivo_id)
    if not db_dispositivo:
        return None
    for campo, valore in dati.model_dump(exclude_unset=True).items():
        setattr(db_dispositivo, campo, valore)
    db.commit()
    db.refresh(db_dispositivo)
    return db_dispositivo


def elimina_dispositivo(db: Session, dispositivo_id: int) -> bool:
    db_dispositivo = get_dispositivo(db, dispositivo_id)
    if not db_dispositivo:
        return False
    db.delete(db_dispositivo)
    db.commit()
    return True


# --- Manutenzione ---

def crea_manutenzione(
    db: Session, dispositivo_id: int, manutenzione: schemas.ManutenzioneCreate
) -> Optional[models.Manutenzione]:
    if not get_dispositivo(db, dispositivo_id):
        return None
    db_manutenzione = models.Manutenzione(**manutenzione.model_dump(), dispositivo_id=dispositivo_id)
    db.add(db_manutenzione)
    db.commit()
    db.refresh(db_manutenzione)
    return db_manutenzione


def lista_manutenzioni(db: Session, dispositivo_id: int) -> List[models.Manutenzione]:
    return list(db.scalars(
        select(models.Manutenzione)
        .where(models.Manutenzione.dispositivo_id == dispositivo_id)
        .order_by(models.Manutenzione.data.desc())
    ).all())


def lista_manutenzioni(db: Session, dispositivo_id: int) -> List[models.Manutenzione]:
    stmt = (
        select(models.Manutenzione)
        .where(models.Manutenzione.dispositivo_id == dispositivo_id)
        .order_by(models.Manutenzione.data.desc())
    )
    return list(db.scalars(stmt).all())


# --- Calibrazione ---

def crea_calibrazione(
    db: Session, dispositivo_id: int, calibrazione: schemas.CalibrazioneCreate
) -> Optional[models.Calibrazione]:
    if not get_dispositivo(db, dispositivo_id):
        return None
    db_calibrazione = models.Calibrazione(**calibrazione.model_dump(), dispositivo_id=dispositivo_id)
    db.add(db_calibrazione)
    db.commit()
    db.refresh(db_calibrazione)
    return db_calibrazione


def lista_calibrazioni(db: Session, dispositivo_id: int) -> List[models.Calibrazione]:
    return list(db.scalars(
        select(models.Calibrazione)
        .where(models.Calibrazione.dispositivo_id == dispositivo_id)
        .order_by(models.Calibrazione.data.desc())
    ).all())


def lista_calibrazioni(db: Session, dispositivo_id: int) -> List[models.Calibrazione]:
    stmt = (
        select(models.Calibrazione)
        .where(models.Calibrazione.dispositivo_id == dispositivo_id)
        .order_by(models.Calibrazione.data.desc())
    )
    return list(db.scalars(stmt).all())


# --- Scadenze (feature "interessante": alert su manutenzioni/calibrazioni in scadenza) ---

def dispositivi_in_scadenza(db: Session, entro_giorni: int = 30) -> List[schemas.ScadenzaItem]:
    oggi = date.today()
    limite = oggi + timedelta(days=entro_giorni)
    risultati: List[schemas.ScadenzaItem] = []

    manutenzioni = db.scalars(
        select(models.Manutenzione).where(
            models.Manutenzione.prossima_scadenza.is_not(None),
            models.Manutenzione.prossima_scadenza <= limite,
        )
    ).all()
    for m in manutenzioni:
        risultati.append(schemas.ScadenzaItem(
            dispositivo_id=m.dispositivo_id,
            dispositivo_nome=m.dispositivo.nome,
            tipo_scadenza="manutenzione",
            data_scadenza=m.prossima_scadenza,
            giorni_rimanenti=(m.prossima_scadenza - oggi).days,
        ))

    calibrazioni = db.scalars(
        select(models.Calibrazione).where(
            models.Calibrazione.prossima_scadenza.is_not(None),
            models.Calibrazione.prossima_scadenza <= limite,
        )
    ).all()
    for c in calibrazioni:
        risultati.append(schemas.ScadenzaItem(
            dispositivo_id=c.dispositivo_id,
            dispositivo_nome=c.dispositivo.nome,
            tipo_scadenza="calibrazione",
            data_scadenza=c.prossima_scadenza,
            giorni_rimanenti=(c.prossima_scadenza - oggi).days,
        ))

    risultati.sort(key=lambda x: x.giorni_rimanenti)
    return risultati