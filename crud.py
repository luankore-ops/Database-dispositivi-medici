"""
crud.py
-------
Funzioni di accesso al database (Create, Read, Update, Delete).

Gestisce:
- utenti;
- reparti;
- fornitori;
- dispositivi medici;
- manutenzioni;
- calibrazioni;
- scadenze.

La logica di integrità dei dati viene gestita qui,
mentre gli endpoint FastAPI trasformano gli errori
in appropriate risposte HTTP.
"""

from datetime import date, timedelta
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import models
import schemas

from auth import hash_password


# ============================================================
# ECCEZIONI
# ============================================================

class DuplicateResourceError(Exception):
    """
    Eccezione utilizzata quando si tenta di creare
    o modificare una risorsa con un valore univoco
    già presente nel database.
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


# ============================================================
# UTENTI
# ============================================================

def lista_utenti(
    db: Session,
) -> List[models.Utente]:
    """
    Restituisce tutti gli utenti.

    Gli utenti sono ordinati per username.
    """

    stmt = (
        select(models.Utente)
        .order_by(models.Utente.username)
    )

    return list(
        db.scalars(stmt).all()
    )


def get_utente(
    db: Session,
    utente_id: int,
) -> Optional[models.Utente]:
    """
    Restituisce un utente tramite ID.
    """

    return db.get(
        models.Utente,
        utente_id,
    )


def get_utente_by_username(
    db: Session,
    username: str,
) -> Optional[models.Utente]:
    """
    Restituisce un utente tramite username.
    """

    stmt = (
        select(models.Utente)
        .where(
            models.Utente.username == username
        )
    )

    return db.scalar(stmt)


def crea_utente(
    db: Session,
    utente: schemas.UtenteCreate,
) -> models.Utente:
    """
    Crea un nuovo utente.

    La password viene trasformata in hash
    prima di essere salvata nel database.
    """

    existing = get_utente_by_username(
        db,
        utente.username,
    )

    if existing:
        raise DuplicateResourceError(
            f"Lo username '{utente.username}' "
            "è già utilizzato."
        )

    db_utente = models.Utente(
        username=utente.username,
        password_hash=hash_password(
            utente.password
        ),
        ruolo=utente.ruolo,
        attivo=utente.attivo,
    )

    db.add(db_utente)

    try:
        db.commit()
        db.refresh(db_utente)

    except IntegrityError:
        db.rollback()

        raise DuplicateResourceError(
            "Impossibile creare l'utente: "
            "username già esistente."
        )

    return db_utente


def conta_amministratori_attivi(
    db: Session,
) -> int:
    """
    Conta gli amministratori attualmente attivi.
    """

    stmt = (
        select(models.Utente)
        .where(
            models.Utente.ruolo
            == models.RuoloUtente.ADMIN,

            models.Utente.attivo.is_(True),
        )
    )

    return len(
        list(db.scalars(stmt).all())
    )


def aggiorna_utente(
    db: Session,
    utente_id: int,
    dati: schemas.UtenteUpdate,
) -> Optional[models.Utente]:
    """
    Aggiorna username, ruolo e/o stato
    di un utente.
    """

    db_utente = get_utente(
        db,
        utente_id,
    )

    if not db_utente:
        return None

    dati_modificati = dati.model_dump(
        exclude_unset=True
    )

    if "username" in dati_modificati:

        nuovo_username = (
            dati_modificati["username"]
        )

        altro_utente = (
            get_utente_by_username(
                db,
                nuovo_username,
            )
        )

        if (
            altro_utente
            and altro_utente.id != utente_id
        ):
            raise DuplicateResourceError(
                f"Lo username "
                f"'{nuovo_username}' "
                "è già utilizzato."
            )

    for campo, valore in dati_modificati.items():

        setattr(
            db_utente,
            campo,
            valore,
        )

    try:
        db.commit()
        db.refresh(db_utente)

    except IntegrityError:
        db.rollback()

        raise DuplicateResourceError(
            "Impossibile aggiornare l'utente."
        )

    return db_utente


def aggiorna_password_utente(
    db: Session,
    utente_id: int,
    nuova_password: str,
) -> Optional[models.Utente]:
    """
    Aggiorna la password di un utente.

    La password non viene mai memorizzata
    in chiaro.
    """

    db_utente = get_utente(
        db,
        utente_id,
    )

    if not db_utente:
        return None

    db_utente.password_hash = hash_password(
        nuova_password
    )

    db.commit()
    db.refresh(db_utente)

    return db_utente


def aggiorna_stato_utente(
    db: Session,
    utente_id: int,
    attivo: bool,
) -> Optional[models.Utente]:
    """
    Attiva o disattiva un utente.
    """

    db_utente = get_utente(
        db,
        utente_id,
    )

    if not db_utente:
        return None

    db_utente.attivo = attivo

    db.commit()
    db.refresh(db_utente)

    return db_utente


# ============================================================
# REPARTI
# ============================================================

def crea_reparto(
    db: Session,
    reparto: schemas.RepartoCreate,
) -> models.Reparto:
    """
    Crea un nuovo reparto.
    """

    existing = db.scalar(
        select(models.Reparto).where(
            models.Reparto.nome
            == reparto.nome
        )
    )

    if existing:
        raise DuplicateResourceError(
            f"Il reparto '{reparto.nome}' "
            "esiste già."
        )

    db_reparto = models.Reparto(
        **reparto.model_dump()
    )

    db.add(db_reparto)

    try:
        db.commit()
        db.refresh(db_reparto)

    except IntegrityError:
        db.rollback()

        raise DuplicateResourceError(
            f"Il reparto '{reparto.nome}' "
            "esiste già."
        )

    return db_reparto


def lista_reparti(
    db: Session,
) -> List[models.Reparto]:
    """
    Restituisce tutti i reparti.
    """

    stmt = (
        select(models.Reparto)
        .order_by(models.Reparto.nome)
    )

    return list(
        db.scalars(stmt).all()
    )


# ============================================================
# FORNITORI
# ============================================================

def crea_fornitore(
    db: Session,
    fornitore: schemas.FornitoreCreate,
) -> models.Fornitore:
    """
    Crea un nuovo fornitore.
    """

    db_fornitore = models.Fornitore(
        **fornitore.model_dump()
    )

    db.add(db_fornitore)

    try:
        db.commit()
        db.refresh(db_fornitore)

    except IntegrityError:
        db.rollback()

        raise DuplicateResourceError(
            "Impossibile creare il fornitore: "
            "i dati violano un vincolo "
            "del database."
        )

    return db_fornitore


def lista_fornitori(
    db: Session,
) -> List[models.Fornitore]:
    """
    Restituisce tutti i fornitori.
    """

    stmt = (
        select(models.Fornitore)
        .order_by(
            models.Fornitore.ragione_sociale
        )
    )

    return list(
        db.scalars(stmt).all()
    )


# ============================================================
# DISPOSITIVI
# ============================================================

def _controlla_unicita_dispositivo(
    db: Session,
    dispositivo: schemas.DispositivoCreate,
) -> None:
    """
    Controlla l'unicità di numero seriale e UDI.
    """

    seriale_esistente = db.scalar(
        select(models.Dispositivo).where(
            models.Dispositivo.numero_seriale
            == dispositivo.numero_seriale
        )
    )

    if seriale_esistente:
        raise DuplicateResourceError(
            "Il numero di serie "
            f"'{dispositivo.numero_seriale}' "
            "è già presente nel database."
        )

    if dispositivo.udi:

        udi_esistente = db.scalar(
            select(models.Dispositivo).where(
                models.Dispositivo.udi
                == dispositivo.udi
            )
        )

        if udi_esistente:
            raise DuplicateResourceError(
                f"L'UDI '{dispositivo.udi}' "
                "è già presente nel database."
            )


def crea_dispositivo(
    db: Session,
    dispositivo: schemas.DispositivoCreate,
) -> models.Dispositivo:
    """
    Crea un nuovo dispositivo medico.
    """

    _controlla_unicita_dispositivo(
        db,
        dispositivo,
    )

    db_dispositivo = models.Dispositivo(
        **dispositivo.model_dump()
    )

    db.add(db_dispositivo)

    try:
        db.commit()
        db.refresh(db_dispositivo)

    except IntegrityError:
        db.rollback()

        raise DuplicateResourceError(
            "Il dispositivo contiene "
            "un valore già presente "
            "nel database."
        )

    return db_dispositivo


def lista_dispositivi(
    db: Session,
    categoria: Optional[str] = None,
    stato: Optional[models.StatoDispositivo] = None,
) -> List[models.Dispositivo]:
    """
    Restituisce i dispositivi, eventualmente
    filtrati per categoria e stato.
    """

    stmt = select(models.Dispositivo)

    if categoria:
        stmt = stmt.where(
            models.Dispositivo.categoria
            == categoria
        )

    if stato:
        stmt = stmt.where(
            models.Dispositivo.stato
            == stato
        )

    stmt = stmt.order_by(
        models.Dispositivo.nome
    )

    return list(
        db.scalars(stmt).all()
    )


def get_dispositivo(
    db: Session,
    dispositivo_id: int,
) -> Optional[models.Dispositivo]:
    """
    Restituisce un dispositivo tramite ID.
    """

    return db.get(
        models.Dispositivo,
        dispositivo_id,
    )


def aggiorna_dispositivo(
    db: Session,
    dispositivo_id: int,
    dati: schemas.DispositivoUpdate,
) -> Optional[models.Dispositivo]:
    """
    Aggiorna un dispositivo esistente.
    """

    db_dispositivo = get_dispositivo(
        db,
        dispositivo_id,
    )

    if not db_dispositivo:
        return None

    dati_modificati = dati.model_dump(
        exclude_unset=True
    )

    # --------------------------------------------------------
    # NUMERO SERIALE
    # --------------------------------------------------------

    if "numero_seriale" in dati_modificati:

        nuovo_seriale = dati_modificati[
            "numero_seriale"
        ]

        seriale_esistente = db.scalar(
            select(models.Dispositivo).where(
                models.Dispositivo.numero_seriale
                == nuovo_seriale,

                models.Dispositivo.id
                != dispositivo_id,
            )
        )

        if seriale_esistente:
            raise DuplicateResourceError(
                "Il numero di serie "
                f"'{nuovo_seriale}' "
                "è già utilizzato "
                "da un altro dispositivo."
            )

    # --------------------------------------------------------
    # UDI
    # --------------------------------------------------------

    if "udi" in dati_modificati:

        nuovo_udi = dati_modificati[
            "udi"
        ]

        if nuovo_udi:

            udi_esistente = db.scalar(
                select(models.Dispositivo).where(
                    models.Dispositivo.udi
                    == nuovo_udi,

                    models.Dispositivo.id
                    != dispositivo_id,
                )
            )

            if udi_esistente:
                raise DuplicateResourceError(
                    f"L'UDI '{nuovo_udi}' "
                    "è già utilizzato "
                    "da un altro dispositivo."
                )

    # --------------------------------------------------------
    # AGGIORNAMENTO
    # --------------------------------------------------------

    for campo, valore in dati_modificati.items():

        setattr(
            db_dispositivo,
            campo,
            valore,
        )

    try:
        db.commit()
        db.refresh(db_dispositivo)

    except IntegrityError:
        db.rollback()

        raise DuplicateResourceError(
            "Impossibile aggiornare "
            "il dispositivo: "
            "uno dei valori inseriti "
            "è già presente nel database."
        )

    return db_dispositivo


def elimina_dispositivo(
    db: Session,
    dispositivo_id: int,
) -> bool:
    """
    Elimina un dispositivo.
    """

    db_dispositivo = get_dispositivo(
        db,
        dispositivo_id,
    )

    if not db_dispositivo:
        return False

    db.delete(db_dispositivo)
    db.commit()

    return True


# ============================================================
# MANUTENZIONI
# ============================================================

def crea_manutenzione(
    db: Session,
    dispositivo_id: int,
    manutenzione: schemas.ManutenzioneCreate,
) -> Optional[models.Manutenzione]:
    """
    Registra una manutenzione.
    """

    if not get_dispositivo(
        db,
        dispositivo_id,
    ):
        return None

    db_manutenzione = models.Manutenzione(
        **manutenzione.model_dump(),
        dispositivo_id=dispositivo_id,
    )

    db.add(db_manutenzione)

    try:
        db.commit()
        db.refresh(db_manutenzione)

    except IntegrityError:
        db.rollback()
        raise

    return db_manutenzione


def lista_manutenzioni(
    db: Session,
    dispositivo_id: int,
) -> List[models.Manutenzione]:
    """
    Restituisce le manutenzioni di un dispositivo.
    """

    stmt = (
        select(models.Manutenzione)
        .where(
            models.Manutenzione.dispositivo_id
            == dispositivo_id
        )
        .order_by(
            models.Manutenzione.data.desc()
        )
    )

    return list(
        db.scalars(stmt).all()
    )


# ============================================================
# CALIBRAZIONI
# ============================================================

def crea_calibrazione(
    db: Session,
    dispositivo_id: int,
    calibrazione: schemas.CalibrazioneCreate,
) -> Optional[models.Calibrazione]:
    """
    Registra una calibrazione.
    """

    if not get_dispositivo(
        db,
        dispositivo_id,
    ):
        return None

    db_calibrazione = models.Calibrazione(
        **calibrazione.model_dump(),
        dispositivo_id=dispositivo_id,
    )

    db.add(db_calibrazione)

    try:
        db.commit()
        db.refresh(db_calibrazione)

    except IntegrityError:
        db.rollback()
        raise

    return db_calibrazione


def lista_calibrazioni(
    db: Session,
    dispositivo_id: int,
) -> List[models.Calibrazione]:
    """
    Restituisce le calibrazioni di un dispositivo.
    """

    stmt = (
        select(models.Calibrazione)
        .where(
            models.Calibrazione.dispositivo_id
            == dispositivo_id
        )
        .order_by(
            models.Calibrazione.data.desc()
        )
    )

    return list(
        db.scalars(stmt).all()
    )


# ============================================================
# SCADENZE
# ============================================================

def dispositivi_in_scadenza(
    db: Session,
    entro_giorni: int = 30,
) -> List[schemas.ScadenzaItem]:
    """
    Restituisce manutenzioni e calibrazioni
    con scadenza entro il numero di giorni
    specificato.
    """

    oggi = date.today()

    limite = (
        oggi
        + timedelta(
            days=entro_giorni
        )
    )

    risultati: List[
        schemas.ScadenzaItem
    ] = []

    # --------------------------------------------------------
    # MANUTENZIONI
    # --------------------------------------------------------

    manutenzioni = db.scalars(
        select(models.Manutenzione).where(
            models.Manutenzione.prossima_scadenza
            .is_not(None),

            models.Manutenzione.prossima_scadenza
            <= limite,
        )
    ).all()

    for manutenzione in manutenzioni:

        risultati.append(
            schemas.ScadenzaItem(
                dispositivo_id=(
                    manutenzione.dispositivo_id
                ),

                dispositivo_nome=(
                    manutenzione.dispositivo.nome
                ),

                tipo_scadenza="manutenzione",

                data_scadenza=(
                    manutenzione.prossima_scadenza
                ),

                giorni_rimanenti=(
                    manutenzione.prossima_scadenza
                    - oggi
                ).days,
            )
        )

    # --------------------------------------------------------
    # CALIBRAZIONI
    # --------------------------------------------------------

    calibrazioni = db.scalars(
        select(models.Calibrazione).where(
            models.Calibrazione.prossima_scadenza
            .is_not(None),

            models.Calibrazione.prossima_scadenza
            <= limite,
        )
    ).all()

    for calibrazione in calibrazioni:

        risultati.append(
            schemas.ScadenzaItem(
                dispositivo_id=(
                    calibrazione.dispositivo_id
                ),

                dispositivo_nome=(
                    calibrazione.dispositivo.nome
                ),

                tipo_scadenza="calibrazione",

                data_scadenza=(
                    calibrazione.prossima_scadenza
                ),

                giorni_rimanenti=(
                    calibrazione.prossima_scadenza
                    - oggi
                ).days,
            )
        )

    # --------------------------------------------------------
    # ORDINAMENTO
    # --------------------------------------------------------

    risultati.sort(
        key=lambda item:
        item.giorni_rimanenti
    )

    return risultati