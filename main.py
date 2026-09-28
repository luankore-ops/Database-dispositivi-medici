"""
main.py
-------
API FastAPI per la gestione dei dispositivi medici.

Funzionalità:
- autenticazione JWT;
- controllo dei ruoli;
- gestione dispositivi;
- gestione manutenzioni;
- gestione calibrazioni;
- gestione reparti;
- gestione fornitori;
- gestione utenti;
- audit log.

Avvio:
    uvicorn main:app --reload

Documentazione:
    http://127.0.0.1:8000/docs
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Query,
)
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import crud
import models
import schemas

from auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    require_roles,
)

from database import (
    get_session,
    init_db,
)

from security import SecurityHeadersMiddleware


# ============================================================
# LIFESPAN
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Inizializza il database all'avvio dell'applicazione.
    """

    init_db()

    yield


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Gestione Dispositivi Medici",
    description=(
        "API per l'inventario, la manutenzione, "
        "la calibrazione e la sicurezza dei "
        "dispositivi medici ospedalieri."
    ),
    version="0.2.0",
    lifespan=lifespan,
)


# ============================================================
# SECURITY HEADERS
# ============================================================

app.add_middleware(
    SecurityHeadersMiddleware
)


# ============================================================
# DATABASE
# ============================================================

def get_db():
    """
    Dependency FastAPI per ottenere una sessione database.
    """

    db = get_session()

    try:
        yield db

    finally:
        db.close()


# ============================================================
# AUDIT LOG
# ============================================================

def registra_audit(
    db: Session,
    utente: models.Utente,
    azione: str,
    tabella: str,
    dettagli: Optional[str] = None,
):
    """
    Registra un'operazione nell'audit log.
    """

    log = models.AuditLog(
        timestamp=datetime.now(
            timezone.utc
        ).replace(
            tzinfo=None
        ),
        utente=utente.username,
        azione=azione,
        tabella=tabella,
        dettagli=dettagli,
    )

    db.add(log)

    db.commit()


# ============================================================
# ROOT
# ============================================================

@app.get(
    "/",
    include_in_schema=False,
)
def root():
    """
    Reindirizza alla documentazione Swagger.
    """

    return RedirectResponse(
        url="/docs"
    )


# ============================================================
# AUTENTICAZIONE
# ============================================================

@app.post(
    "/login",
    tags=["Autenticazione"],
)
def login(
    username: str,
    password: str,
    db: Session = Depends(get_db),
):
    """
    Autentica un utente e restituisce un JWT.
    """

    user = authenticate_user(
        db,
        username,
        password,
    )

    if user is None:

        raise HTTPException(
            status_code=401,
            detail="Username o password non corretti.",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    token = create_access_token(
        user
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.ruolo.value,
            "attivo": user.attivo,
        },
    }


@app.get(
    "/me",
    tags=["Autenticazione"],
)
def me(
    current_user: models.Utente = Depends(
        get_current_user
    ),
):
    """
    Restituisce le informazioni
    dell'utente autenticato.
    """

    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.ruolo.value,
        "attivo": current_user.attivo,
    }


# ============================================================
# UTENTI
# ============================================================

@app.get(
    "/utenti",
    response_model=List[schemas.UtenteRead],
    tags=["Utenti"],
)
def lista_utenti(
    db: Session = Depends(get_db),
    current_user: models.Utente = Depends(
        require_roles(
            models.RuoloUtente.ADMIN
        )
    ),
):
    """
    Restituisce tutti gli utenti.

    Accesso:
        ADMIN
    """

    return crud.lista_utenti(
        db
    )


@app.get(
    "/utenti/{utente_id}",
    response_model=schemas.UtenteRead,
    tags=["Utenti"],
)
def get_utente(
    utente_id: int,
    db: Session = Depends(get_db),
    current_user: models.Utente = Depends(
        require_roles(
            models.RuoloUtente.ADMIN
        )
    ),
):
    """
    Restituisce un singolo utente.
    """

    utente = crud.get_utente(
        db,
        utente_id,
    )

    if not utente:

        raise HTTPException(
            status_code=404,
            detail="Utente non trovato.",
        )

    return utente


@app.post(
    "/utenti",
    response_model=schemas.UtenteRead,
    status_code=201,
    tags=["Utenti"],
)
def crea_utente(
    utente: schemas.UtenteCreate,
    db: Session = Depends(get_db),
    current_user: models.Utente = Depends(
        require_roles(
            models.RuoloUtente.ADMIN
        )
    ),
):
    """
    Crea un nuovo account utente.

    Accesso:
        ADMIN
    """

    username = utente.username.strip()

    if not username:

        raise HTTPException(
            status_code=422,
            detail="Lo username non può essere vuoto.",
        )

    utente_esistente = (
        crud.get_utente_by_username(
            db,
            username,
        )
    )

    if utente_esistente:

        raise HTTPException(
            status_code=409,
            detail=(
                f"Lo username '{username}' "
                "è già utilizzato."
            ),
        )

    dati = utente.model_copy(
        update={
            "username": username
        }
    )

    try:

        nuovo_utente = crud.crea_utente(
            db,
            dati,
        )

        registra_audit(
            db=db,
            utente=current_user,
            azione="CREATE",
            tabella="utenti",
            dettagli=(
                f"Creato utente "
                f"'{nuovo_utente.username}' "
                f"con ruolo "
                f"'{nuovo_utente.ruolo.value}'."
            ),
        )

        return nuovo_utente

    except IntegrityError:

        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "Impossibile creare l'utente: "
                "username già esistente."
            ),
        )


@app.put(
    "/utenti/{utente_id}",
    response_model=schemas.UtenteRead,
    tags=["Utenti"],
)
def aggiorna_utente(
    utente_id: int,
    dati: schemas.UtenteUpdate,
    db: Session = Depends(get_db),
    current_user: models.Utente = Depends(
        require_roles(
            models.RuoloUtente.ADMIN
        )
    ),
):
    """
    Modifica username, ruolo o stato di un utente.

    Accesso:
        ADMIN
    """

    utente = crud.get_utente(
        db,
        utente_id,
    )

    if not utente:

        raise HTTPException(
            status_code=404,
            detail="Utente non trovato.",
        )

    valori = dati.model_dump(
        exclude_unset=True
    )

    # --------------------------------------------------------
    # USERNAME
    # --------------------------------------------------------

    if "username" in valori:

        username = valori["username"].strip()

        if not username:

            raise HTTPException(
                status_code=422,
                detail=(
                    "Lo username non può "
                    "essere vuoto."
                ),
            )

        altro_utente = (
            crud.get_utente_by_username(
                db,
                username,
            )
        )

        if (
            altro_utente
            and altro_utente.id != utente.id
        ):

            raise HTTPException(
                status_code=409,
                detail=(
                    f"Lo username '{username}' "
                    "è già utilizzato."
                ),
            )

        valori["username"] = username

    # --------------------------------------------------------
    # PROTEZIONE ACCOUNT CORRENTE
    # --------------------------------------------------------

    nuova_attivazione = valori.get(
        "attivo",
        utente.attivo,
    )

    nuovo_ruolo = valori.get(
        "ruolo",
        utente.ruolo,
    )

    # Un admin non può disattivare sé stesso.
    if (
        utente.id == current_user.id
        and nuova_attivazione is False
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Non puoi disattivare "
                "il tuo stesso account."
            ),
        )

    # Un admin non può togliere a sé stesso
    # il ruolo di amministratore.
    if (
        utente.id == current_user.id
        and nuovo_ruolo
        != models.RuoloUtente.ADMIN
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Non puoi rimuovere il ruolo "
                "admin dal tuo stesso account."
            ),
        )

    # --------------------------------------------------------
    # PROTEZIONE ULTIMO AMMINISTRATORE
    # --------------------------------------------------------

    sta_per_perdere_admin = (
        utente.ruolo
        == models.RuoloUtente.ADMIN
        and (
            nuovo_ruolo
            != models.RuoloUtente.ADMIN
            or nuova_attivazione is False
        )
    )

    if sta_per_perdere_admin:

        admin_attivi = (
            crud.conta_amministratori_attivi(
                db
            )
        )

        if admin_attivi <= 1:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Operazione non consentita: "
                    "deve rimanere almeno "
                    "un amministratore attivo."
                ),
            )

    # --------------------------------------------------------
    # AGGIORNAMENTO
    # --------------------------------------------------------

    dati_validati = schemas.UtenteUpdate(
        **valori
    )

    try:

        utente_aggiornato = (
            crud.aggiorna_utente(
                db,
                utente_id,
                dati_validati,
            )
        )

        if not utente_aggiornato:

            raise HTTPException(
                status_code=404,
                detail="Utente non trovato.",
            )

        registra_audit(
            db=db,
            utente=current_user,
            azione="UPDATE",
            tabella="utenti",
            dettagli=(
                f"Aggiornato utente "
                f"'{utente_aggiornato.username}'."
            ),
        )

        return utente_aggiornato

    except IntegrityError:

        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "Impossibile aggiornare "
                "l'utente."
            ),
        )


@app.put(
    "/utenti/{utente_id}/password",
    response_model=schemas.UtenteRead,
    tags=["Utenti"],
)
def aggiorna_password_utente(
    utente_id: int,
    dati: schemas.UtentePasswordUpdate,
    db: Session = Depends(get_db),
    current_user: models.Utente = Depends(
        require_roles(
            models.RuoloUtente.ADMIN
        )
    ),
):
    """
    Cambia la password di un utente.

    Accesso:
        ADMIN
    """

    utente = crud.get_utente(
        db,
        utente_id,
    )

    if not utente:

        raise HTTPException(
            status_code=404,
            detail="Utente non trovato.",
        )

    utente_aggiornato = (
        crud.aggiorna_password_utente(
            db,
            utente_id,
            dati.password,
        )
    )

    if not utente_aggiornato:

        raise HTTPException(
            status_code=404,
            detail="Utente non trovato.",
        )

    registra_audit(
        db=db,
        utente=current_user,
        azione="PASSWORD_CHANGE",
        tabella="utenti",
        dettagli=(
            f"Modificata password "
            f"dell'utente "
            f"'{utente.username}'."
        ),
    )

    return utente_aggiornato


@app.put(
    "/utenti/{utente_id}/stato",
    response_model=schemas.UtenteRead,
    tags=["Utenti"],
)
def aggiorna_stato_utente(
    utente_id: int,
    dati: schemas.UtenteStatoUpdate,
    db: Session = Depends(get_db),
    current_user: models.Utente = Depends(
        require_roles(
            models.RuoloUtente.ADMIN
        )
    ),
):
    """
    Attiva o disattiva un account.

    Accesso:
        ADMIN
    """

    utente = crud.get_utente(
        db,
        utente_id,
    )

    if not utente:

        raise HTTPException(
            status_code=404,
            detail="Utente non trovato.",
        )

    # --------------------------------------------------------
    # NON PUOI DISATTIVARE TE STESSO
    # --------------------------------------------------------

    if (
        utente.id == current_user.id
        and not dati.attivo
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Non puoi disattivare "
                "il tuo stesso account."
            ),
        )

    # --------------------------------------------------------
    # NON DISATTIVARE L'ULTIMO ADMIN
    # --------------------------------------------------------

    if (
        utente.ruolo
        == models.RuoloUtente.ADMIN
        and not dati.attivo
    ):

        admin_attivi = (
            crud.conta_amministratori_attivi(
                db
            )
        )

        if admin_attivi <= 1:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Non puoi disattivare "
                    "l'ultimo amministratore "
                    "attivo."
                ),
            )

    utente_aggiornato = (
        crud.aggiorna_stato_utente(
            db,
            utente_id,
            dati.attivo,
        )
    )

    if not utente_aggiornato:

        raise HTTPException(
            status_code=404,
            detail="Utente non trovato.",
        )

    azione = (
        "ACTIVATE"
        if dati.attivo
        else "DEACTIVATE"
    )

    registra_audit(
        db=db,
        utente=current_user,
        azione=azione,
        tabella="utenti",
        dettagli=(
            f"Utente "
            f"'{utente.username}' "
            f"{'attivato' if dati.attivo else 'disattivato'}."
        ),
    )

    return utente_aggiornato


# ============================================================
# AUDIT LOG
# ============================================================

@app.get(
    "/audit-log",
    tags=["Sicurezza"],
)
def lista_audit_log(
    db: Session = Depends(get_db),
    current_user: models.Utente = Depends(
        require_roles(
            models.RuoloUtente.ADMIN
        )
    ),
):
    """
    Restituisce l'audit log.

    Accesso:
        ADMIN
    """

    logs = (
        db.query(
            models.AuditLog
        )
        .order_by(
            models.AuditLog.timestamp.desc()
        )
        .limit(500)
        .all()
    )

    return [
        {
            "id": log.id,
            "timestamp": log.timestamp,
            "utente": log.utente,
            "azione": log.azione,
            "tabella": log.tabella,
            "dettagli": log.dettagli,
        }
        for log in logs
    ]


# ============================================================
# REPARTI
# ============================================================

@app.post(
    "/reparti",
    response_model=schemas.RepartoRead,
    tags=["Reparti"],
)
def crea_reparto(
    reparto: schemas.RepartoCreate,
    db: Session = Depends(get_db),
    current_user: models.Utente = Depends(
        require_roles(
            models.RuoloUtente.ADMIN,
            models.RuoloUtente.TECNICO,
        )
    ),
):
    reparto_creato = crud.crea_reparto(
        db,
        reparto,
    )

    registra_audit(
        db=db,
        utente=current_user,
        azione="CREATE",
        tabella="reparti",
        dettagli=(
            f"Creato reparto "
            f"'{reparto_creato.nome}'."
        ),
    )

    return reparto_creato


@app.get(
    "/reparti",
    response_model=List[schemas.RepartoRead],
    tags=["Reparti"],
)
def lista_reparti(
    db: Session = Depends(get_db),
    current_user: models.Utente = Depends(
        get_current_user
    ),
):
    return crud.lista_reparti(
        db
    )


# ============================================================
# FORNITORI
# ============================================================

@app.post(
    "/fornitori",
    response_model=schemas.FornitoreRead,
    tags=["Fornitori"],
)
def crea_fornitore(
    fornitore: schemas.FornitoreCreate,
    db: Session = Depends(get_db),
    current_user: models.Utente = Depends(
        require_roles(
            models.RuoloUtente.ADMIN,
            models.RuoloUtente.TECNICO,
        )
    ),
):
    fornitore_creato = crud.crea_fornitore(
        db,
        fornitore,
    )

    registra_audit(
        db=db,
        utente=current_user,
        azione="CREATE",
        tabella="fornitori",
        dettagli=(
            "Creato fornitore "
            f"'{fornitore_creato.ragione_sociale}'."
        ),
    )

    return fornitore_creato


@app.get(
    "/fornitori",
    response_model=List[schemas.FornitoreRead],
    tags=["Fornitori"],
)
def lista_fornitori(
    db: Session = Depends(get_db),
    current_user: models.Utente = Depends(
        get_current_user
    ),
):
    return crud.lista_fornitori(
        db
    )


# ============================================================
# DISPOSITIVI
# ============================================================

@app.post(
    "/dispositivi",
    response_model=schemas.DispositivoRead,
    tags=["Dispositivi"],
)
def crea_dispositivo(
    dispositivo: schemas.DispositivoCreate,
    db: Session = Depends(get_db),
    current_user: models.Utente = Depends(
        require_roles(
            models.RuoloUtente.ADMIN,
            models.RuoloUtente.TECNICO,
        )
    ),
):
    try:

        nuovo_dispositivo = (
            crud.crea_dispositivo(
                db,
                dispositivo,
            )
        )

        registra_audit(
            db=db,
            utente=current_user,
            azione="CREATE",
            tabella="dispositivi",
            dettagli=(
                f"Creato dispositivo "
                f"'{nuovo_dispositivo.nome}' "
                f"(ID {nuovo_dispositivo.id})."
            ),
        )

        return nuovo_dispositivo

    except crud.DuplicateResourceError as exc:

        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    except IntegrityError:

        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "Numero seriale o UDI "
                "già presenti nel database."
            ),
        )


@app.get(
    "/dispositivi",
    response_model=List[schemas.DispositivoRead],
    tags=["Dispositivi"],
)
def lista_dispositivi(
    categoria: Optional[str] = None,
    stato: Optional[
        models.StatoDispositivo
    ] = None,
    db: Session = Depends(get_db),
    current_user: models.Utente = Depends(
        get_current_user
    ),
):
    return crud.lista_dispositivi(
        db,
        categoria=categoria,
        stato=stato,
    )


@app.get(
    "/dispositivi/scadenze",
    response_model=List[schemas.ScadenzaItem],
    tags=["Dispositivi"],
)
def dispositivi_in_scadenza(
    entro_giorni: int = Query(
        30,
        ge=0,
        le=3650,
        description=(
            "Numero di giorni entro cui "
            "cercare le scadenze."
        ),
    ),
    db: Session = Depends(get_db),
    current_user: models.Utente = Depends(
        get_current_user
    ),
):
    return crud.dispositivi_in_scadenza(
        db,
        entro_giorni=entro_giorni,
    )


@app.get(
    "/dispositivi/{dispositivo_id}",
    response_model=schemas.DispositivoRead,
    tags=["Dispositivi"],
)
def get_dispositivo(
    dispositivo_id: int,
    db: Session = Depends(get_db),
    current_user: models.Utente = Depends(
        get_current_user
    ),
):
    dispositivo = crud.get_dispositivo(
        db,
        dispositivo_id,
    )

    if not dispositivo:

        raise HTTPException(
            status_code=404,
            detail="Dispositivo non trovato.",
        )

    return dispositivo


@app.put(
    "/dispositivi/{dispositivo_id}",
    response_model=schemas.DispositivoRead,
    tags=["Dispositivi"],
)
def aggiorna_dispositivo(
    dispositivo_id: int,
    dati: schemas.DispositivoUpdate,
    db: Session = Depends(get_db),
    current_user: models.Utente = Depends(
        require_roles(
            models.RuoloUtente.ADMIN,
            models.RuoloUtente.TECNICO,
        )
    ),
):
    try:

        dispositivo = (
            crud.aggiorna_dispositivo(
                db,
                dispositivo_id,
                dati,
            )
        )

        if not dispositivo:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Dispositivo non trovato."
                ),
            )

        registra_audit(
            db=db,
            utente=current_user,
            azione="UPDATE",
            tabella="dispositivi",
            dettagli=(
                f"Aggiornato dispositivo "
                f"'{dispositivo.nome}' "
                f"(ID {dispositivo.id})."
            ),
        )

        return dispositivo

    except crud.DuplicateResourceError as exc:

        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    except IntegrityError:

        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "Numero seriale o UDI "
                "già presenti nel database."
            ),
        )


@app.delete(
    "/dispositivi/{dispositivo_id}",
    status_code=204,
    tags=["Dispositivi"],
)
def elimina_dispositivo(
    dispositivo_id: int,
    db: Session = Depends(get_db),
    current_user: models.Utente = Depends(
        require_roles(
            models.RuoloUtente.ADMIN
        )
    ),
):
    dispositivo = crud.get_dispositivo(
        db,
        dispositivo_id,
    )

    if not dispositivo:

        raise HTTPException(
            status_code=404,
            detail="Dispositivo non trovato.",
        )

    nome = dispositivo.nome

    if not crud.elimina_dispositivo(
        db,
        dispositivo_id,
    ):

        raise HTTPException(
            status_code=404,
            detail="Dispositivo non trovato.",
        )

    registra_audit(
        db=db,
        utente=current_user,
        azione="DELETE",
        tabella="dispositivi",
        dettagli=(
            f"Eliminato dispositivo "
            f"'{nome}' "
            f"(ID {dispositivo_id})."
        ),
    )


# ============================================================
# MANUTENZIONI
# ============================================================

@app.post(
    "/dispositivi/{dispositivo_id}/manutenzioni",
    response_model=schemas.ManutenzioneRead,
    tags=["Manutenzioni"],
)
def crea_manutenzione(
    dispositivo_id: int,
    manutenzione: schemas.ManutenzioneCreate,
    db: Session = Depends(get_db),
    current_user: models.Utente = Depends(
        require_roles(
            models.RuoloUtente.ADMIN,
            models.RuoloUtente.TECNICO,
        )
    ),
):
    db_manutenzione = (
        crud.crea_manutenzione(
            db,
            dispositivo_id,
            manutenzione,
        )
    )

    if not db_manutenzione:

        raise HTTPException(
            status_code=404,
            detail="Dispositivo non trovato.",
        )

    registra_audit(
        db=db,
        utente=current_user,
        azione="CREATE",
        tabella="manutenzioni",
        dettagli=(
            f"Registrata manutenzione "
            f"per dispositivo ID "
            f"{dispositivo_id}."
        ),
    )

    return db_manutenzione


@app.get(
    "/dispositivi/{dispositivo_id}/manutenzioni",
    response_model=List[schemas.ManutenzioneRead],
    tags=["Manutenzioni"],
)
def lista_manutenzioni(
    dispositivo_id: int,
    db: Session = Depends(get_db),
    current_user: models.Utente = Depends(
        get_current_user
    ),
):
    if not crud.get_dispositivo(
        db,
        dispositivo_id,
    ):

        raise HTTPException(
            status_code=404,
            detail="Dispositivo non trovato.",
        )

    return crud.lista_manutenzioni(
        db,
        dispositivo_id,
    )


# ============================================================
# CALIBRAZIONI
# ============================================================

@app.post(
    "/dispositivi/{dispositivo_id}/calibrazioni",
    response_model=schemas.CalibrazioneRead,
    tags=["Calibrazioni"],
)
def crea_calibrazione(
    dispositivo_id: int,
    calibrazione: schemas.CalibrazioneCreate,
    db: Session = Depends(get_db),
    current_user: models.Utente = Depends(
        require_roles(
            models.RuoloUtente.ADMIN,
            models.RuoloUtente.TECNICO,
        )
    ),
):
    db_calibrazione = (
        crud.crea_calibrazione(
            db,
            dispositivo_id,
            calibrazione,
        )
    )

    if not db_calibrazione:

        raise HTTPException(
            status_code=404,
            detail="Dispositivo non trovato.",
        )

    registra_audit(
        db=db,
        utente=current_user,
        azione="CREATE",
        tabella="calibrazioni",
        dettagli=(
            f"Registrata calibrazione "
            f"per dispositivo ID "
            f"{dispositivo_id}."
        ),
    )

    return db_calibrazione


@app.get(
    "/dispositivi/{dispositivo_id}/calibrazioni",
    response_model=List[schemas.CalibrazioneRead],
    tags=["Calibrazioni"],
)
def lista_calibrazioni(
    dispositivo_id: int,
    db: Session = Depends(get_db),
    current_user: models.Utente = Depends(
        get_current_user
    ),
):
    if not crud.get_dispositivo(
        db,
        dispositivo_id,
    ):

        raise HTTPException(
            status_code=404,
            detail="Dispositivo non trovato.",
        )

    return crud.lista_calibrazioni(
        db,
        dispositivo_id,
    )