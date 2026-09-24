"""
seed_data.py — Popola il database con dati di esempio realistici.
Eseguire con: python seed_data.py
"""

from datetime import date

from database import init_db, get_session
from models import (
    Dispositivo, Reparto, Fornitore, Manutenzione, Calibrazione,
    StatoDispositivo, TipoManutenzione, EsitoVerifica,
)


def seed() -> None:
    init_db()
    session = get_session()

    if session.query(Dispositivo).first():
        print("Il database contiene già dati. Seed non eseguito.")
        session.close()
        return

    # --- Reparti ---
    radiologia = Reparto(nome="Radiologia", piano="1")
    terapia_intensiva = Reparto(nome="Terapia Intensiva", piano="2")
    cardiologia = Reparto(nome="Cardiologia", piano="3")
    session.add_all([radiologia, terapia_intensiva, cardiologia])

    # --- Fornitori ---
    ge_healthcare = Fornitore(ragione_sociale="GE Healthcare", email_contatto="assistenza@gehealthcare.com")
    philips = Fornitore(ragione_sociale="Philips Healthcare", email_contatto="support@philips.com")
    session.add_all([ge_healthcare, philips])
    session.flush()  # per ottenere gli id prima di usarli nelle relazioni

    # --- Dispositivi ---
    tac = Dispositivo(
        nome="Tomografo Computerizzato",
        categoria="Diagnostica per immagini",
        numero_seriale="GE-TAC-2023-001",
        udi="(01)00844588003288(11)230501(21)SN00234",
        produttore="GE Healthcare",
        modello="Revolution EVO",
        data_acquisto=date(2023, 5, 1),
        costo=850000.0,
        data_scadenza_garanzia=date(2026, 5, 1),
        stato=StatoDispositivo.IN_USO,
        reparto=radiologia,
        fornitore=ge_healthcare,
    )

    ventilatore = Dispositivo(
        nome="Ventilatore Polmonare",
        categoria="Terapia",
        numero_seriale="PH-VENT-2022-014",
        udi="(01)08717648012345(11)220310(21)SN00891",
        produttore="Philips Healthcare",
        modello="Respironics V680",
        data_acquisto=date(2022, 3, 10),
        costo=32000.0,
        data_scadenza_garanzia=date(2025, 3, 10),
        stato=StatoDispositivo.IN_USO,
        reparto=terapia_intensiva,
        fornitore=philips,
    )

    ecg = Dispositivo(
        nome="Elettrocardiografo",
        categoria="Monitoraggio",
        numero_seriale="GE-ECG-2021-007",
        udi="(01)00840682012340(11)210620(21)SN00456",
        produttore="GE Healthcare",
        modello="MAC 2000",
        data_acquisto=date(2021, 6, 20),
        costo=8500.0,
        data_scadenza_garanzia=date(2024, 6, 20),
        stato=StatoDispositivo.MANUTENZIONE,
        reparto=cardiologia,
        fornitore=ge_healthcare,
    )

    session.add_all([tac, ventilatore, ecg])
    session.flush()

    # --- Manutenzioni ---
    session.add_all([
        Manutenzione(
            dispositivo=tac, data=date(2026, 1, 15), tipo=TipoManutenzione.PREVENTIVA,
            tecnico="M. Rossi", descrizione="Controllo periodico semestrale",
            prossima_scadenza=date(2026, 7, 15),
        ),
        Manutenzione(
            dispositivo=ecg, data=date(2026, 9, 10), tipo=TipoManutenzione.CORRETTIVA,
            tecnico="A. Bianchi", descrizione="Sostituzione cavo derivazioni",
            prossima_scadenza=None,
        ),
    ])

    # --- Calibrazioni ---
    session.add_all([
        Calibrazione(
            dispositivo=ventilatore, data=date(2026, 4, 1), esito=EsitoVerifica.CONFORME,
            ente_certificatore="Metrica Srl", prossima_scadenza=date(2027, 4, 1),
        ),
        Calibrazione(
            dispositivo=tac, data=date(2025, 11, 20), esito=EsitoVerifica.CONFORME,
            ente_certificatore="TÜV Italia", prossima_scadenza=date(2026, 11, 20),
        ),
    ])

    session.commit()
    session.close()
    print("Database popolato con dati di esempio (3 dispositivi, 2 manutenzioni, 2 calibrazioni).")


if __name__ == "__main__":
    seed()
