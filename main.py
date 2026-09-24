"""
main.py — API FastAPI per la gestione dei dispositivi medici

Avvio: uvicorn main:app --reload
Documentazione interattiva: http://127.0.0.1:8000/docs
"""

from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

import crud
import schemas
import models
from database import get_session, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Gestione Dispositivi Medici",
    description="API per l'inventario, la manutenzione e la calibrazione dei dispositivi medici ospedalieri",
    version="0.1.0",
    lifespan=lifespan,
)


def get_db():
    db = get_session()
    try:
        yield db
    finally:
        db.close()


@app.get("/", include_in_schema=False)
def root():
    """Reindirizza alla documentazione interattiva (Swagger UI)."""
    return RedirectResponse(url="/docs")


# --- Reparti ---

@app.post("/reparti", response_model=schemas.RepartoRead, tags=["Reparti"])
def crea_reparto(reparto: schemas.RepartoCreate, db: Session = Depends(get_db)):
    return crud.crea_reparto(db, reparto)


@app.get("/reparti", response_model=List[schemas.RepartoRead], tags=["Reparti"])
def lista_reparti(db: Session = Depends(get_db)):
    return crud.lista_reparti(db)


# --- Fornitori ---

@app.post("/fornitori", response_model=schemas.FornitoreRead, tags=["Fornitori"])
def crea_fornitore(fornitore: schemas.FornitoreCreate, db: Session = Depends(get_db)):
    return crud.crea_fornitore(db, fornitore)


@app.get("/fornitori", response_model=List[schemas.FornitoreRead], tags=["Fornitori"])
def lista_fornitori(db: Session = Depends(get_db)):
    return crud.lista_fornitori(db)


# --- Dispositivi ---

@app.post("/dispositivi", response_model=schemas.DispositivoRead, tags=["Dispositivi"])
def crea_dispositivo(dispositivo: schemas.DispositivoCreate, db: Session = Depends(get_db)):
    return crud.crea_dispositivo(db, dispositivo)


@app.get("/dispositivi", response_model=List[schemas.DispositivoRead], tags=["Dispositivi"])
def lista_dispositivi(
    categoria: Optional[str] = None,
    stato: Optional[models.StatoDispositivo] = None,
    db: Session = Depends(get_db),
):
    return crud.lista_dispositivi(db, categoria=categoria, stato=stato)


@app.get("/dispositivi/scadenze", response_model=List[schemas.ScadenzaItem], tags=["Dispositivi"])
def dispositivi_in_scadenza(
    entro_giorni: int = Query(30, description="Numero di giorni entro cui cercare le scadenze"),
    db: Session = Depends(get_db),
):
    """Restituisce manutenzioni e calibrazioni in scadenza entro N giorni, ordinate per urgenza."""
    return crud.dispositivi_in_scadenza(db, entro_giorni=entro_giorni)


@app.get("/dispositivi/{dispositivo_id}", response_model=schemas.DispositivoRead, tags=["Dispositivi"])
def get_dispositivo(dispositivo_id: int, db: Session = Depends(get_db)):
    db_dispositivo = crud.get_dispositivo(db, dispositivo_id)
    if not db_dispositivo:
        raise HTTPException(status_code=404, detail="Dispositivo non trovato")
    return db_dispositivo


@app.put("/dispositivi/{dispositivo_id}", response_model=schemas.DispositivoRead, tags=["Dispositivi"])
def aggiorna_dispositivo(dispositivo_id: int, dati: schemas.DispositivoUpdate, db: Session = Depends(get_db)):
    db_dispositivo = crud.aggiorna_dispositivo(db, dispositivo_id, dati)
    if not db_dispositivo:
        raise HTTPException(status_code=404, detail="Dispositivo non trovato")
    return db_dispositivo


@app.delete("/dispositivi/{dispositivo_id}", status_code=204, tags=["Dispositivi"])
def elimina_dispositivo(dispositivo_id: int, db: Session = Depends(get_db)):
    if not crud.elimina_dispositivo(db, dispositivo_id):
        raise HTTPException(status_code=404, detail="Dispositivo non trovato")


# --- Manutenzioni ---

@app.post("/dispositivi/{dispositivo_id}/manutenzioni", response_model=schemas.ManutenzioneRead, tags=["Manutenzioni"])
def crea_manutenzione(dispositivo_id: int, manutenzione: schemas.ManutenzioneCreate, db: Session = Depends(get_db)):
    db_manutenzione = crud.crea_manutenzione(db, dispositivo_id, manutenzione)
    if not db_manutenzione:
        raise HTTPException(status_code=404, detail="Dispositivo non trovato")
    return db_manutenzione


@app.get("/dispositivi/{dispositivo_id}/manutenzioni", response_model=List[schemas.ManutenzioneRead], tags=["Manutenzioni"])
def lista_manutenzioni(dispositivo_id: int, db: Session = Depends(get_db)):
    if not crud.get_dispositivo(db, dispositivo_id):
        raise HTTPException(status_code=404, detail="Dispositivo non trovato")
    return crud.lista_manutenzioni(db, dispositivo_id)


# --- Calibrazioni ---

@app.post("/dispositivi/{dispositivo_id}/calibrazioni", response_model=schemas.CalibrazioneRead, tags=["Calibrazioni"])
def crea_calibrazione(dispositivo_id: int, calibrazione: schemas.CalibrazioneCreate, db: Session = Depends(get_db)):
    db_calibrazione = crud.crea_calibrazione(db, dispositivo_id, calibrazione)
    if not db_calibrazione:
        raise HTTPException(status_code=404, detail="Dispositivo non trovato")
    return db_calibrazione


@app.get("/dispositivi/{dispositivo_id}/calibrazioni", response_model=List[schemas.CalibrazioneRead], tags=["Calibrazioni"])
def lista_calibrazioni(dispositivo_id: int, db: Session = Depends(get_db)):
    if not crud.get_dispositivo(db, dispositivo_id):
        raise HTTPException(status_code=404, detail="Dispositivo non trovato")
    return crud.lista_calibrazioni(db, dispositivo_id)