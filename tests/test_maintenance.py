"""
tests/test_maintenance.py
-------------------------
Test automatici della gestione delle manutenzioni.

Regole RBAC:
- ADMIN   -> può creare e leggere manutenzioni
- TECNICO -> può creare e leggere manutenzioni
- LETTORE -> può leggere, ma non creare
"""

from datetime import date


def dispositivo_payload():
    """
    Restituisce un payload valido per creare
    un dispositivo di test.
    """

    return {
        "nome": "Monitor Multiparametrico Test",
        "categoria": "Monitoraggio",
        "numero_seriale": "MANUT-SN-001",
        "udi": "MANUT-UDI-001",
        "produttore": "Test Medical",
        "modello": "TM-100",
        "data_acquisto": "2025-01-15",
        "costo": 5000.00,
        "data_scadenza_garanzia": "2028-01-15",
        "stato": "in_uso",
    }


def manutenzione_payload():
    """
    Restituisce un payload valido per creare
    una manutenzione.
    """

    return {
        "data": "2026-09-26",
        "tipo": "preventiva",
        "tecnico": "Tecnico Test",
        "descrizione": "Manutenzione preventiva ordinaria.",
        "prossima_scadenza": "2027-09-26",
    }


def crea_dispositivo_test(
    client,
    headers,
):
    """
    Crea un dispositivo utilizzabile
    nei test delle manutenzioni.
    """

    response = client.post(
        "/dispositivi",
        json=dispositivo_payload(),
        headers=headers,
    )

    assert response.status_code == 200

    return response.json()


# ============================================================
# CREAZIONE MANUTENZIONI
# ============================================================

def test_admin_puo_creare_manutenzione(
    client,
    admin_user,
    login_admin,
):
    """
    Un amministratore può registrare
    una manutenzione.
    """

    dispositivo = crea_dispositivo_test(
        client,
        login_admin,
    )

    dispositivo_id = dispositivo["id"]

    response = client.post(
        f"/dispositivi/{dispositivo_id}/manutenzioni",
        json=manutenzione_payload(),
        headers=login_admin,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["dispositivo_id"] == dispositivo_id
    assert data["data"] == "2026-09-26"
    assert data["tipo"] == "preventiva"
    assert data["tecnico"] == "Tecnico Test"
    assert (
        data["descrizione"]
        == "Manutenzione preventiva ordinaria."
    )
    assert data["prossima_scadenza"] == "2027-09-26"
    assert "id" in data


def test_tecnico_puo_creare_manutenzione(
    client,
    tecnico_user,
    login_tecnico,
):
    """
    Un tecnico può registrare
    una manutenzione.
    """

    dispositivo = crea_dispositivo_test(
        client,
        login_tecnico,
    )

    dispositivo_id = dispositivo["id"]

    response = client.post(
        f"/dispositivi/{dispositivo_id}/manutenzioni",
        json=manutenzione_payload(),
        headers=login_tecnico,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["dispositivo_id"] == dispositivo_id


def test_lettore_non_puo_creare_manutenzione(
    client,
    admin_user,
    lettore_user,
    login_admin,
    login_lettore,
):
    """
    Un lettore non può registrare
    una nuova manutenzione.
    """

    dispositivo = crea_dispositivo_test(
        client,
        login_admin,
    )

    dispositivo_id = dispositivo["id"]

    response = client.post(
        f"/dispositivi/{dispositivo_id}/manutenzioni",
        json=manutenzione_payload(),
        headers=login_lettore,
    )

    assert response.status_code == 403


def test_creazione_manutenzione_senza_token(
    client,
):
    """
    Una richiesta senza autenticazione
    deve essere rifiutata.
    """

    response = client.post(
        "/dispositivi/1/manutenzioni",
        json=manutenzione_payload(),
    )

    assert response.status_code == 401


# ============================================================
# LETTURA MANUTENZIONI
# ============================================================

def test_admin_puo_leggere_manutenzioni(
    client,
    admin_user,
    login_admin,
):
    """
    Un amministratore può leggere
    le manutenzioni di un dispositivo.
    """

    dispositivo = crea_dispositivo_test(
        client,
        login_admin,
    )

    dispositivo_id = dispositivo["id"]

    create_response = client.post(
        f"/dispositivi/{dispositivo_id}/manutenzioni",
        json=manutenzione_payload(),
        headers=login_admin,
    )

    assert create_response.status_code == 200

    response = client.get(
        f"/dispositivi/{dispositivo_id}/manutenzioni",
        headers=login_admin,
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["dispositivo_id"] == dispositivo_id


def test_tecnico_puo_leggere_manutenzioni(
    client,
    tecnico_user,
    login_tecnico,
):
    """
    Un tecnico può leggere
    le manutenzioni.
    """

    dispositivo = crea_dispositivo_test(
        client,
        login_tecnico,
    )

    dispositivo_id = dispositivo["id"]

    create_response = client.post(
        f"/dispositivi/{dispositivo_id}/manutenzioni",
        json=manutenzione_payload(),
        headers=login_tecnico,
    )

    assert create_response.status_code == 200

    response = client.get(
        f"/dispositivi/{dispositivo_id}/manutenzioni",
        headers=login_tecnico,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["dispositivo_id"] == dispositivo_id


def test_lettore_puo_leggere_manutenzioni(
    client,
    admin_user,
    lettore_user,
    login_admin,
    login_lettore,
):
    """
    Un lettore può consultare
    le manutenzioni.
    """

    dispositivo = crea_dispositivo_test(
        client,
        login_admin,
    )

    dispositivo_id = dispositivo["id"]

    create_response = client.post(
        f"/dispositivi/{dispositivo_id}/manutenzioni",
        json=manutenzione_payload(),
        headers=login_admin,
    )

    assert create_response.status_code == 200

    response = client.get(
        f"/dispositivi/{dispositivo_id}/manutenzioni",
        headers=login_lettore,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["dispositivo_id"] == dispositivo_id


def test_lettura_manutenzioni_senza_token(
    client,
):
    """
    Una richiesta senza autenticazione
    deve essere rifiutata.
    """

    response = client.get(
        "/dispositivi/1/manutenzioni",
    )

    assert response.status_code == 401


# ============================================================
# DISPOSITIVO INESISTENTE
# ============================================================

def test_creazione_manutenzione_dispositivo_inesistente(
    client,
    admin_user,
    login_admin,
):
    """
    Non è possibile creare una manutenzione
    per un dispositivo inesistente.
    """

    response = client.post(
        "/dispositivi/999999/manutenzioni",
        json=manutenzione_payload(),
        headers=login_admin,
    )

    assert response.status_code == 404


def test_lettura_manutenzioni_dispositivo_inesistente(
    client,
    admin_user,
    login_admin,
):
    """
    La lettura delle manutenzioni di un
    dispositivo inesistente deve restituire 404.
    """

    response = client.get(
        "/dispositivi/999999/manutenzioni",
        headers=login_admin,
    )

    assert response.status_code == 404


# ============================================================
# PIÙ MANUTENZIONI
# ============================================================

def test_dispositivo_puo_avere_piu_manutenzioni(
    client,
    admin_user,
    login_admin,
):
    """
    Un dispositivo può avere più registrazioni
    di manutenzione.
    """

    dispositivo = crea_dispositivo_test(
        client,
        login_admin,
    )

    dispositivo_id = dispositivo["id"]

    manutenzione_1 = {
        "data": "2026-01-15",
        "tipo": "preventiva",
        "tecnico": "Tecnico A",
        "descrizione": "Prima manutenzione.",
        "prossima_scadenza": "2027-01-15",
    }

    manutenzione_2 = {
        "data": "2026-06-20",
        "tipo": "correttiva",
        "tecnico": "Tecnico B",
        "descrizione": "Riparazione guasto.",
        "prossima_scadenza": None,
    }

    response_1 = client.post(
        f"/dispositivi/{dispositivo_id}/manutenzioni",
        json=manutenzione_1,
        headers=login_admin,
    )

    response_2 = client.post(
        f"/dispositivi/{dispositivo_id}/manutenzioni",
        json=manutenzione_2,
        headers=login_admin,
    )

    assert response_1.status_code == 200
    assert response_2.status_code == 200

    response = client.get(
        f"/dispositivi/{dispositivo_id}/manutenzioni",
        headers=login_admin,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2


# ============================================================
# TIPI DI MANUTENZIONE
# ============================================================

def test_manutenzione_preventiva(
    client,
    admin_user,
    login_admin,
):
    """
    Verifica la registrazione di una
    manutenzione preventiva.
    """

    dispositivo = crea_dispositivo_test(
        client,
        login_admin,
    )

    response = client.post(
        f"/dispositivi/{dispositivo['id']}/manutenzioni",
        json={
            "data": "2026-09-26",
            "tipo": "preventiva",
            "tecnico": "Tecnico Preventivo",
            "descrizione": "Controllo periodico.",
            "prossima_scadenza": "2027-09-26",
        },
        headers=login_admin,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["tipo"] == "preventiva"


def test_manutenzione_correttiva(
    client,
    admin_user,
    login_admin,
):
    """
    Verifica la registrazione di una
    manutenzione correttiva.
    """

    dispositivo = crea_dispositivo_test(
        client,
        login_admin,
    )

    response = client.post(
        f"/dispositivi/{dispositivo['id']}/manutenzioni",
        json={
            "data": "2026-09-26",
            "tipo": "correttiva",
            "tecnico": "Tecnico Riparazione",
            "descrizione": "Riparazione di un guasto.",
            "prossima_scadenza": None,
        },
        headers=login_admin,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["tipo"] == "correttiva"


# ============================================================
# VALIDAZIONE DATI
# ============================================================

def test_manutenzione_data_mancante(
    client,
    admin_user,
    login_admin,
):
    """
    Il campo data è obbligatorio.
    """

    dispositivo = crea_dispositivo_test(
        client,
        login_admin,
    )

    payload = {
        "tipo": "preventiva",
        "tecnico": "Tecnico Test",
        "descrizione": "Test.",
    }

    response = client.post(
        f"/dispositivi/{dispositivo['id']}/manutenzioni",
        json=payload,
        headers=login_admin,
    )

    assert response.status_code == 422


def test_manutenzione_tipo_mancante(
    client,
    admin_user,
    login_admin,
):
    """
    Il campo tipo è obbligatorio.
    """

    dispositivo = crea_dispositivo_test(
        client,
        login_admin,
    )

    payload = {
        "data": "2026-09-26",
        "tecnico": "Tecnico Test",
        "descrizione": "Test.",
    }

    response = client.post(
        f"/dispositivi/{dispositivo['id']}/manutenzioni",
        json=payload,
        headers=login_admin,
    )

    assert response.status_code == 422


def test_manutenzione_tipo_non_valido(
    client,
    admin_user,
    login_admin,
):
    """
    Il tipo di manutenzione deve essere
    preventiva oppure correttiva.
    """

    dispositivo = crea_dispositivo_test(
        client,
        login_admin,
    )

    payload = {
        "data": "2026-09-26",
        "tipo": "non_valido",
        "tecnico": "Tecnico Test",
        "descrizione": "Test.",
    }

    response = client.post(
        f"/dispositivi/{dispositivo['id']}/manutenzioni",
        json=payload,
        headers=login_admin,
    )

    assert response.status_code == 422


def test_manutenzione_descrizione_troppo_lunga(
    client,
    admin_user,
    login_admin,
):
    """
    La descrizione non può superare
    2000 caratteri.
    """

    dispositivo = crea_dispositivo_test(
        client,
        login_admin,
    )

    payload = {
        "data": "2026-09-26",
        "tipo": "preventiva",
        "tecnico": "Tecnico Test",
        "descrizione": "A" * 2001,
    }

    response = client.post(
        f"/dispositivi/{dispositivo['id']}/manutenzioni",
        json=payload,
        headers=login_admin,
    )

    assert response.status_code == 422


def test_manutenzione_tecnico_troppo_lungo(
    client,
    admin_user,
    login_admin,
):
    """
    Il nome del tecnico non può superare
    100 caratteri.
    """

    dispositivo = crea_dispositivo_test(
        client,
        login_admin,
    )

    payload = {
        "data": "2026-09-26",
        "tipo": "preventiva",
        "tecnico": "A" * 101,
        "descrizione": "Test.",
    }

    response = client.post(
        f"/dispositivi/{dispositivo['id']}/manutenzioni",
        json=payload,
        headers=login_admin,
    )

    assert response.status_code == 422


# ============================================================
# CAMPI OPZIONALI
# ============================================================

def test_manutenzione_campi_opzionali_assenti(
    client,
    admin_user,
    login_admin,
):
    """
    Tecnico, descrizione e prossima scadenza
    sono campi opzionali.
    """

    dispositivo = crea_dispositivo_test(
        client,
        login_admin,
    )

    payload = {
        "data": "2026-09-26",
        "tipo": "preventiva",
    }

    response = client.post(
        f"/dispositivi/{dispositivo['id']}/manutenzioni",
        json=payload,
        headers=login_admin,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["tecnico"] is None
    assert data["descrizione"] is None
    assert data["prossima_scadenza"] is None


# ============================================================
# AUDIT LOG
# ============================================================

def test_creazione_manutenzione_registra_audit_log(
    client,
    admin_user,
    login_admin,
):
    """
    La creazione di una manutenzione
    deve generare una voce nell'audit log.
    """

    dispositivo = crea_dispositivo_test(
        client,
        login_admin,
    )

    dispositivo_id = dispositivo["id"]

    response = client.post(
        f"/dispositivi/{dispositivo_id}/manutenzioni",
        json=manutenzione_payload(),
        headers=login_admin,
    )

    assert response.status_code == 200

    audit_response = client.get(
        "/audit-log",
        headers=login_admin,
    )

    assert audit_response.status_code == 200

    logs = audit_response.json()

    manutenzione_logs = [
        log
        for log in logs
        if (
            log["tabella"] == "manutenzioni"
            and log["azione"] == "CREATE"
        )
    ]

    assert len(manutenzione_logs) >= 1

    assert any(
        str(dispositivo_id)
        in (log["dettagli"] or "")
        for log in manutenzione_logs
    )